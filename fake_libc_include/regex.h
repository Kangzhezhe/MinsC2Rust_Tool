#include "_fake_defines.h"
#include "_fake_typedefs.h"

struct re_pattern_buffer
  {
  int re_nsub;
 
  };

typedef struct re_pattern_buffer regex_t;

typedef struct
{
  int rm_so;  /* Byte offset from string's start to substring's start.  */
  int rm_eo;  /* Byte offset from string's start to substring's end.  */
} regmatch_t;