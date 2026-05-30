/*
 * This file is needed because in Python3.13+ some exported symbols
 * inside of import.c that are not part of cpython's stable ABI were
 * removed entirely. As such import_mini.c adds the removed ABI back,
 * but ported to use the stable ABI as much as possible for support
 * on future versions of cpython.
 */
#include "import_mini.h"
#include <windows.h>


#if (PY_VERSION_HEX >= 0x030D00B0)
/*
 * Most of the code below was code removed in one of the beta builds
 * of cpython 3.13 and added back (with changes) to support for the
 * updated ABI inside of import.c.
 */
#include <internal/pycore_importdl.h>
#include <internal/pycore_object.h>
#include <internal/pycore_interp.h>

#define EXTENSIONS(interp) (interp)->runtime->imports.extensions
#define MODULES_BY_INDEX(interp) \
    (interp)->imports.modules_by_index

#if (PY_VERSION_HEX < 0x030E0000)
void
_Py_SetImmortalUntracked(PyObject *op)
{
#ifdef Py_DEBUG
    // For strings, use _PyUnicode_InternImmortal instead.
    if (PyUnicode_CheckExact(op)) {
        assert(PyUnicode_CHECK_INTERNED(op) == SSTATE_INTERNED_IMMORTAL
            || PyUnicode_CHECK_INTERNED(op) == SSTATE_INTERNED_IMMORTAL_STATIC);
    }
#endif
#ifdef Py_GIL_DISABLED
    op->ob_tid = _Py_UNOWNED_TID;
    op->ob_ref_local = _Py_IMMORTAL_REFCNT_LOCAL;
    op->ob_ref_shared = 0;
#else
    op->ob_refcnt = _Py_IMMORTAL_REFCNT;
#endif
}
#endif

static bool
is_interpreter_isolated(PyInterpreterState *interp)
{
    return !(interp == interp->runtime->interpreters.main)
        && !(interp->feature_flags & Py_RTFLAGS_USE_MAIN_OBMALLOC)
        && interp->ceval.own_gil;
}

static void
_set_module_index(PyModuleDef *def, Py_ssize_t index)
{
    assert(index > 0);
    if (index == def->m_base.m_index) {
        /* There's nothing to do. */
    }
    else if (def->m_base.m_index == 0) {
        /* It should have been initialized by PyModuleDef_Init().
         * We assert here to catch this in dev, but keep going otherwise. */
        assert(def->m_base.m_index != 0);
        def->m_base.m_index = index;
    }
    else {
        /* It was already set for a different module.
         * We replace the old value. */
        assert(def->m_base.m_index > 0);
        def->m_base.m_index = index;
    }
}

static int
_modules_by_index_set(PyInterpreterState *interp,
                      Py_ssize_t index, PyObject *module)
{
    assert(index > 0);

    if (MODULES_BY_INDEX(interp) == NULL) {
        MODULES_BY_INDEX(interp) = PyList_New(0);
        if (MODULES_BY_INDEX(interp) == NULL) {
            return -1;
        }
    }

    while (PyList_GET_SIZE(MODULES_BY_INDEX(interp)) <= index) {
        if (PyList_Append(MODULES_BY_INDEX(interp), Py_None) < 0) {
            return -1;
        }
    }

    return PyList_SetItem(MODULES_BY_INDEX(interp), index, Py_NewRef(module));
}

/* Magic for extension modules (built-in as well as dynamically
   loaded).  To prevent initializing an extension module more than
   once, we keep a static dictionary 'extensions' keyed by the tuple
   (module name, module name)  (for built-in modules) or by
   (filename, module name) (for dynamically loaded modules), containing these
   modules.  A copy of the module's dictionary is stored by calling
   fix_up_extension() immediately after the module initialization
   function succeeds.  A copy can be retrieved from there by calling
   import_find_extension().

   Modules which do support multiple initialization set their m_size
   field to a non-negative number (indicating the size of the
   module-specific state). They are still recorded in the extensions
   dictionary, to avoid loading shared libraries twice.
*/

typedef struct cached_m_dict {
    /* A shallow copy of the original module's __dict__. */
    PyObject *copied;
    /* The interpreter that owns the copy. */
    int64_t interpid;
} *cached_m_dict_t;

struct extensions_cache_value {
    PyModuleDef *def;

    /* The function used to re-initialize the module.
       This is only set for legacy (single-phase init) extension modules
       and only used for those that support multiple initializations
       (m_size >= 0).
       It is set by update_global_state_for_extension(). */
    PyModInitFunction m_init;

    /* The module's index into its interpreter's modules_by_index cache.
       This is set for all extension modules but only used for legacy ones.
       (See PyInterpreterState.modules_by_index for more info.) */
    Py_ssize_t m_index;

    /* A copy of the module's __dict__ after the first time it was loaded.
       This is only set/used for legacy modules that do not support
       multiple initializations.
       It is set exclusively by fixup_cached_def(). */
    cached_m_dict_t m_dict;
    struct cached_m_dict _m_dict;

    _Py_ext_module_origin origin;

#ifdef Py_GIL_DISABLED
    /* The module's md_gil slot, for legacy modules that are reinitialized from
       m_dict rather than calling their initialization function again. */
    void *md_gil;
#endif
};

static struct extensions_cache_value *
alloc_extensions_cache_value(void)
{
    struct extensions_cache_value *value
            = PyMem_RawMalloc(sizeof(struct extensions_cache_value));
    if (value == NULL) {
        PyErr_NoMemory();
        return NULL;
    }
    *value = (struct extensions_cache_value){0};
    return value;
}

static void
free_extensions_cache_value(struct extensions_cache_value *value)
{
    PyMem_RawFree(value);
}

static void
fixup_cached_def(struct extensions_cache_value *value)
{
    /* For the moment, the values in the def's m_base may belong
     * to another module, and we're replacing them here.  This can
     * cause problems later if the old module is reloaded.
     *
     * Also, we don't decref any old cached values first when we
     * replace them here, in case we need to restore them in the
     * near future.  Instead, the caller is responsible for wrapping
     * this up by calling cleanup_old_cached_def() or
     * restore_old_cached_def() if there was an error. */
    PyModuleDef *def = value->def;
    assert(def != NULL);

    /* We assume that all module defs are statically allocated
       and will never be freed.  Otherwise, we would incref here. */
    _Py_SetImmortalUntracked((PyObject *)def);

    def->m_base.m_init = value->m_init;

    assert(value->m_index > 0);
    _set_module_index(def, value->m_index);

    /* Different modules can share the same def, so we can't just
     * expect m_copy to be NULL. */
    assert(def->m_base.m_copy == NULL
           || def->m_base.m_init == NULL
           || value->m_dict != NULL);
    if (value->m_dict != NULL) {
        assert(value->m_dict->copied != NULL);
        /* As noted above, we don't first decref the old value, if any. */
        def->m_base.m_copy = Py_NewRef(value->m_dict->copied);
    }
}

static void
restore_old_cached_def(PyModuleDef* def, PyModuleDef_Base* oldbase)
{
  def->m_base = *oldbase;
}

static void
cleanup_old_cached_def(PyModuleDef_Base* oldbase)
{
  Py_XDECREF(oldbase->m_copy);
}

static void
del_cached_def(struct extensions_cache_value *value)
{
    /* If we hadn't made the stored defs immortal, we would decref here.
       However, this decref would be problematic if the module def were
       dynamically allocated, it were the last ref, and this function
       were called with an interpreter other than the def's owner. */
    assert(value->def == NULL || _Py_IsImmortal(value->def));

    Py_XDECREF(value->def->m_base.m_copy);
    value->def->m_base.m_copy = NULL;
}

static int
init_cached_m_dict(struct extensions_cache_value *value, PyObject *m_dict)
{
    assert(value != NULL);
    /* This should only have been called without an m_dict already set. */
    assert(value->m_dict == NULL);
    if (m_dict == NULL) {
        return 0;
    }
    assert(PyDict_Check(m_dict));
    assert(value->origin != _Py_ext_module_origin_CORE);

    PyInterpreterState *interp = PyInterpreterState_Get();
    assert(!is_interpreter_isolated(interp));

    /* XXX gh-88216: The copied dict is owned by the current
     * interpreter.  That's a problem if the interpreter has
     * its own obmalloc state or if the module is successfully
     * imported into such an interpreter.  If the interpreter
     * has its own GIL then there may be data races and
     * PyImport_ClearModulesByIndex() can crash.  Normally,
     * a single-phase init module cannot be imported in an
     * isolated interpreter, but there are ways around that.
     * Hence, heere be dragons!  Ideally we would instead do
     * something like make a read-only, immortal copy of the
     * dict using PyMem_RawMalloc() and store *that* in m_copy.
     * Then we'd need to make sure to clear that when the
     * runtime is finalized, rather than in
     * PyImport_ClearModulesByIndex(). */
    PyObject *copied = PyDict_Copy(m_dict);
    if (copied == NULL) {
        /* We expect this can only be "out of memory". */
        return -1;
    }
    // XXX We may want to make the copy immortal.

    value->_m_dict = (struct cached_m_dict){
        .copied=copied,
        .interpid=interp->id,
    };

    value->m_dict = &value->_m_dict;
    return 0;
}

static void
del_cached_m_dict(struct extensions_cache_value *value)
{
    if (value->m_dict != NULL) {
        assert(value->m_dict == &value->_m_dict);
        assert(value->m_dict->copied != NULL);
        /* In the future we can take advantage of m_dict->interpid
         * to decref the dict using the owning interpreter. */
        Py_XDECREF(value->m_dict->copied);
        value->m_dict = NULL;
    }
}

static void
del_extensions_cache_value(struct extensions_cache_value* value)
{
  if (value != NULL) {
    del_cached_m_dict(value);
    del_cached_def(value);
    free_extensions_cache_value(value);
  }
}

static void *
hashtable_key_from_2_strings(PyObject *str1, PyObject *str2, const char sep)
{
    Py_ssize_t str1_len, str2_len;
    const char *str1_data = PyUnicode_AsUTF8AndSize(str1, &str1_len);
    const char *str2_data = PyUnicode_AsUTF8AndSize(str2, &str2_len);
    if (str1_data == NULL || str2_data == NULL) {
        return NULL;
    }
    /* Make sure sep and the NULL byte won't cause an overflow. */
    assert(SIZE_MAX - str1_len - str2_len > 2);
    size_t size = str1_len + 1 + str2_len + 1;

    // XXX Use a buffer if it's a temp value (every case but "set").
    char *key = PyMem_RawMalloc(size);
    if (key == NULL) {
        PyErr_NoMemory();
        return NULL;
    }

    strncpy(key, str1_data, str1_len);
    key[str1_len] = sep;
    strncpy(key + str1_len + 1, str2_data, str2_len + 1);
    assert(strlen(key) == size - 1);
    return key;
}

static Py_uhash_t
hashtable_hash_str(const void *key)
{
#if (PY_VERSION_HEX >= 0x030E00A0)
    return Py_HashBuffer(key, strlen((const char*)key));
#else
    return _Py_HashBytes(key, strlen((const char *)key));
#endif
}

static int
hashtable_compare_str(const void *key1, const void *key2)
{
    return strcmp((const char *)key1, (const char *)key2) == 0;
}

static void
hashtable_destroy_str(void *ptr)
{
    PyMem_RawFree(ptr);
}

#define HTSEP ':'

static int
_extensions_cache_init(PyInterpreterState *interp)
{
    _Py_hashtable_allocator_t alloc = {PyMem_RawMalloc, PyMem_RawFree};
    EXTENSIONS(interp).hashtable = _Py_hashtable_new_full(
        hashtable_hash_str,
        hashtable_compare_str,
        hashtable_destroy_str,  // key
        (_Py_hashtable_destroy_func)del_extensions_cache_value,  // value
        &alloc
    );
    if (EXTENSIONS(interp).hashtable == NULL) {
        PyErr_NoMemory();
        return -1;
    }
    return 0;
}

static _Py_hashtable_entry_t *
_extensions_cache_find_unlocked(PyInterpreterState *interp, PyObject *path, PyObject *name,
                                void **p_key)
{
    if (EXTENSIONS(interp).hashtable == NULL) {
        return NULL;
    }
    void *key = hashtable_key_from_2_strings(path, name, HTSEP);
    if (key == NULL) {
        return NULL;
    }
    _Py_hashtable_entry_t *entry =
            _Py_hashtable_get_entry(EXTENSIONS(interp).hashtable, key);
    if (p_key != NULL) {
        *p_key = key;
    }
    else {
        hashtable_destroy_str(key);
    }
    return entry;
}

static inline void
extensions_lock_acquire(PyInterpreterState *interp)
{
	PyMutex_Lock(&EXTENSIONS(interp).mutex);
}

static inline void
extensions_lock_release(PyInterpreterState *interp)
{
	PyMutex_Unlock(&EXTENSIONS(interp).mutex);
}

/* This can only fail with "out of memory". */
static struct extensions_cache_value *
_extensions_cache_set(PyInterpreterState *interp, PyObject *path, PyObject *name,
                      PyModuleDef *def, PyModInitFunction m_init,
                      Py_ssize_t m_index, PyObject *m_dict,
                      _Py_ext_module_origin origin, void *md_gil)
{
    struct extensions_cache_value *value = NULL;
    void *key = NULL;
    struct extensions_cache_value *newvalue = NULL;
    PyModuleDef_Base olddefbase = def->m_base;

    assert(def != NULL);
    assert(m_init == NULL || m_dict == NULL);
    /* We expect the same symbol to be used and the shared object file
     * to have remained loaded, so it must be the same pointer. */
    assert(def->m_base.m_init == NULL || def->m_base.m_init == m_init);
    /* For now we don't worry about comparing value->m_copy. */
    assert(def->m_base.m_copy == NULL || m_dict != NULL);
    assert((origin == _Py_ext_module_origin_DYNAMIC) == (name != path));
    assert(origin != _Py_ext_module_origin_CORE || m_dict == NULL);

    extensions_lock_acquire(interp);

    if (EXTENSIONS(interp).hashtable == NULL) {
        if (_extensions_cache_init(interp) < 0) {
            goto finally;
        }
    }

    /* Create a cached value to populate for the module. */
    _Py_hashtable_entry_t *entry =
            _extensions_cache_find_unlocked(interp, path, name, &key);
    value = entry == NULL
        ? NULL
        : (struct extensions_cache_value *)entry->value;
    /* We should never be updating an existing cache value. */
    assert(value == NULL);
    if (value != NULL) {
        PyErr_Format(PyExc_SystemError,
                     "extension module %R is already cached", name);
        goto finally;
    }
    newvalue = alloc_extensions_cache_value();
    if (newvalue == NULL) {
        goto finally;
    }

    /* Populate the new cache value data. */
    *newvalue = (struct extensions_cache_value){
        .def=def,
        .m_init=m_init,
        .m_index=m_index,
        /* m_dict is set by set_cached_m_dict(). */
        .origin=origin,
#ifdef Py_GIL_DISABLED
        .md_gil=md_gil,
#endif
    };
#ifndef Py_GIL_DISABLED
    (void)md_gil;
#endif
    if (init_cached_m_dict(newvalue, m_dict) < 0) {
        goto finally;
    }
    fixup_cached_def(newvalue);

    if (entry == NULL) {
        /* It was never added. */
        if (_Py_hashtable_set(EXTENSIONS(interp).hashtable, key, newvalue) < 0) {
            PyErr_NoMemory();
            goto finally;
        }
        /* The hashtable owns the key now. */
        key = NULL;
    }
    else if (value == NULL) {
        /* It was previously deleted. */
        entry->value = newvalue;
    }
    else {
        /* We are updating the entry for an existing module. */
        /* We expect def to be static, so it must be the same pointer. */
        assert(value->def == def);
        /* We expect the same symbol to be used and the shared object file
         * to have remained loaded, so it must be the same pointer. */
        assert(value->m_init == m_init);
        /* The same module can't switch between caching __dict__ and not. */
        assert((value->m_dict == NULL) == (m_dict == NULL));
        /* This shouldn't ever happen. */
        Py_UNREACHABLE();
    }

    value = newvalue;

finally:
    if (value == NULL) {
        restore_old_cached_def(def, &olddefbase);
        if (newvalue != NULL) {
            del_extensions_cache_value(newvalue);
        }
    }
    else {
        cleanup_old_cached_def(&olddefbase);
    }

    extensions_lock_release(interp);
    if (key != NULL) {
        hashtable_destroy_str(key);
    }

    return value;
}

static inline int
is_core_module(PyInterpreterState *interp, PyObject *name, PyObject *path)
{
	/*
	 * This might be called before the core dict copies are in place,
	 * so we can't rely on get_core_module_dict() here.
	 */
  if (path == name) {
    if (PyUnicode_CompareWithASCIIString(name, "sys") == 0) {
      return 1;
    }
    if (PyUnicode_CompareWithASCIIString(name, "builtins") == 0) {
      return 1;
    }
  }
  return 0;
}

static int
fix_up_extension(PyObject* mod, PyObject* name, PyObject* filename)
{
	if (mod == NULL || !PyModule_Check(mod)) {
		PyErr_BadInternalCall();
		return -1;
	}

	struct PyModuleDef* def = PyModule_GetDef(mod);
	if (!def) {
		PyErr_BadInternalCall();
		return -1;
	}

	PyThreadState* tstate = PyThreadState_Get();
	// PyThreadState* tstate = _PyThreadState_GET();
	if (_modules_by_index_set(tstate->interp, def->m_base.m_index, mod) < 0) {
		return -1;
	}

	// bpo-44050: Extensions and def->m_base.m_copy can be updated
	// when the extension module doesn't support sub-interpreters.
	if (def->m_size == -1) {
		if (!is_core_module(tstate->interp, name, filename)) {
			assert(PyUnicode_CompareWithASCIIString(name, "sys") != 0);
			assert(PyUnicode_CompareWithASCIIString(name, "builtins") != 0);
			if (def->m_base.m_copy) {
				/* Somebody already imported the module,
					 likely under a different name.
					 XXX this should really not happen. */
				Py_CLEAR(def->m_base.m_copy);
			}
			PyObject* dict = PyModule_GetDict(mod);
			if (dict == NULL) {
				return -1;
			}
			def->m_base.m_copy = PyDict_Copy(dict);
			if (def->m_base.m_copy == NULL) {
				return -1;
			}
    }
  }

	// XXX Why special-case the main interpreter?
	if ((tstate->interp == tstate->interp->runtime->interpreters.main) || def->m_size == -1) {
		if (_extensions_cache_set(
      tstate->interp, filename, name, def, (PyModInitFunction)def->m_base.m_init,
      def->m_base.m_index, PyModule_GetDict(mod), _Py_ext_module_origin_DYNAMIC, &tstate->interp->_gil) < 0) {
			return -1;
		}
	}

	return 0;
}

int _PyImport_FixupExtensionObject(PyObject *m, PyObject *name1, PyObject *name2, PyObject *modules) {
  if (PyObject_SetItem(modules, name1, m) < 0) {
    return -1;
  }

  if (fix_up_extension(m, name1, name2) < 0) {
    PyMapping_DelItem(modules, name1);
    return -1;
  }

  return 0;
}

#endif
/*
 * to compile _memimporter in python < 3.13 it must be outside of the
 * PY_VERSION_HEX >= 3.13 conditional compile block above.
 */
#ifndef Py_BUILD_CORE_BUILTIN
const char*
_PyImport_SwapPackageContext(const char* newcontext)
{
#if (PY_VERSION_HEX >= 0x030C0000)
	// PyGILState_STATE gil_state = PyGILState_Ensure();  // Ensure GIL is held
	PyInterpreterState *is = PyInterpreterState_Get();
#ifndef HAVE_THREAD_LOCAL
	PyThread_acquire_lock(is->runtime->imports.extensions.mutex, WAIT_LOCK);
#endif
	const char* oldcontext = (is->runtime->imports.pkgcontext);
	(is->runtime->imports.pkgcontext) = newcontext;
#else
	/* On Python 3.11 or older we do this instead. */
	const char* oldcontext = _Py_PackageContext;
	_Py_PackageContext = newcontext;
#endif
#if (PY_VERSION_HEX >= 0x030C0000)
#ifndef HAVE_THREAD_LOCAL
	PyThread_release_lock(is->runtime->imports.extensions.mutex);
#endif
#endif

	// PyGILState_Release(gil_state);  // Release the GIL
	return oldcontext;
}
#endif
