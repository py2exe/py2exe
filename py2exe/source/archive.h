/*
 *	   Copyright (c) 2000, 2001 Thomas Heller
 *
 * Permission is hereby granted, free of charge, to any person obtaining
 * a copy of this software and associated documentation files (the
 * "Software"), to deal in the Software without restriction, including
 * without limitation the rights to use, copy, modify, merge, publish,
 * distribute, sublicense, and/or sell copies of the Software, and to
 * permit persons to whom the Software is furnished to do so, subject to
 * the following conditions:
 *
 * The above copyright notice and this permission notice shall be
 * included in all copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
 * EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
 * MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
 * NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
 * LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
 * OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
 * WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
 */

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
