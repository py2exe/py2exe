#pragma pack(1)

/* zip-archive headers
 * See: http://www.pkware.com/appnote.html
 */

struct eof_cdir {
    long tag;	/* must be 0x06054b50 */
    short disknum;
    short firstdisk;
    short nTotalCDirThis;
    short nTotalCDir;
    long nBytesCDir;
    long ofsCDir;
    short commentlen;
};

struct cdir {
    long tag;	/* must be 0x02014b50 */
    short version_made;
    short version_extract;
    short gp_bitflag;
    short comp_method;
    short last_mod_file_time;
    short last_mod_file_date;
    long crc32;
    long comp_size;
    long uncomp_size;
    short fname_length;
    short extra_length;
    short comment_length;
    short disknum_start;
    short int_file_attr;
    long ext_file_attr;
    long ofs_local_header;
};

struct fhdr {
    long tag;	/* must be 0x04034b50 */
    short version_needed;
    short flags;
    short method;
    short last_mod_file_time;
    short last_mod_file_date;
    long crc32;
    long comp_size;
    long uncomp_size;
    short fname_length;
    short extra_length;
};

#pragma pack()
