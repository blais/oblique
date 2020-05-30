// Helpers for in-memory data structures. We built everything as protos
// in-memory and resolve references and types as a second stage.

#ifndef _OBLIQUE_DATA_H_
#define _OBLIQUE_DATA_H_

#include <string>

namespace oblique {
namespace proto {
class Ref;
}  // namespace proto
namespace data {

// The type name of the default item type.
extern const char* kItemType;
extern const char* kTypeType;

// Build a type/ident ref key from a Ref.
std::string MakeRefKey(const proto::Ref& ref);

}  //  namespace data
}  //  namespace oblique

#endif // _OBLIQUE_DATA_H_
