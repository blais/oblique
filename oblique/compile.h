// Algorithms processing the parsed data structure. This akin to compiling our
// DSL, i.e., resolving references, checking for high-level errors and types.

#ifndef _OBLIQUE_COMPILE_H_
#define _OBLIQUE_COMPILE_H_

#include "oblique/data.pb.h"
#include "oblique/data.h"

#include <list>

#include "absl/status/status.h"

namespace oblique {

// Apply all the compilation steps and resolve references in the database.
// This mutates the database and inserts errors as well.
absl::Status Resolve(proto::Database* db, bool ignore_ref_to_undeclared);

}  //  namespace oblique

#endif // _OBLIQUE_COMPILE_H_
