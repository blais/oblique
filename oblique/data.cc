#include "oblique/data.h"
#include "oblique/data.pb.h"

#include "absl/strings/str_cat.h"

namespace oblique {
namespace data {

const char* kTypeType = "type";
const char* kItemType = "item";

std::string MakeRefKey(const proto::Ref& ref) {
  return absl::StrCat(ref.type(), "/", ref.ident());
}

}  // namespace data
}  // namespace oblique
