#include "oblique/compile.h"
#include "oblique/data.h"
#include "oblique/data.pb.h"

#include <memory>
#include <utility>
#include <sstream>

#include "absl/container/flat_hash_map.h"
#include "absl/status/status.h"
#include "absl/strings/str_cat.h"

namespace oblique {
using std::string;
using std::cout;
using std::endl;

absl::Status Resolve(proto::Database* db, bool ignore_ref_to_undeclared) {
  assert(db);

  std::list<proto::Error*> errors;

  // Create a fast mapping of type ref key to object.
  absl::flat_hash_map<string, const proto::Type*> type_map;
  for (const auto& typ : db->type()) {
    type_map.insert({typ.type(), &typ});
  }

  // Process each of the objects, fixing up the ident fields using the seqeucne
  // numbers, and handling the IGNORE types.
  int32_t sequence = -1;
  for (proto::Object& obj : *db->mutable_object()) {
    ++sequence;

    // Check that the type has been declared.
    auto type_iter = type_map.find(obj.id().type());
    if (type_iter == type_map.end()) {
      std::ostringstream oss;
      oss << "Definition for undeclared type '" << data::MakeRefKey(obj.id()) << "'";
      auto error = db->mutable_error()->Add();
      error->set_lineno(obj.lineno());
      error->set_error_message(oss.str());
      continue;
    }

    // Declaration of ignored types have been parsed as object declarations. We
    // need to undo this on the objects, by restoring the object type to the
    // default type and re-inserting the reference at the front.
    if (type_iter->second->flavor() == proto::TypeFlavor::IGNORE) {
      string refkey = absl::StrCat(obj.id().type(), "/", obj.id().ident());
      obj.set_contents(absl::StrCat(refkey, " ", obj.contents()));
      auto* id = obj.mutable_id();
      id->set_type(data::kItemType);
      id->set_ident(absl::StrCat(sequence));
    }

    // Fill in auto object ids using sequence number.
    if (obj.id().ident().empty()) {
      obj.mutable_id()->set_ident(absl::StrCat(sequence));
    }
  }

  // Create a fast mapping of type/ident ref key to object.
  absl::flat_hash_map<string, const proto::Object*> object_map;
  for (const auto& obj : db->object()) {
    string refkey = absl::StrCat(obj.id().type(), "/", obj.id().ident());
    object_map.insert({refkey, &obj});
  }

  // Process each of the objects, resolving references.
  for (proto::Object& obj : *db->mutable_object()) {
    // Resolve references. We look up all the references in the database and
    // move them from the referencing object's 'unresolved_refs' to its 'refs'
    // when found, and leave them where they are when not found.
    std::vector<proto::Ref*> unresolved;
    unresolved.reserve(obj.unresolved_refs().size());
    while (obj.unresolved_refs().size() > 0) {
      unresolved.push_back(obj.mutable_unresolved_refs()->ReleaseLast());
    }
    for (auto* ref : unresolved) {
      // first look up the type of this outbound ref to find out how we ought to
      // treat it.
      auto type_iter = type_map.find(ref->type());
      if (type_iter == type_map.end()) {
        if (ignore_ref_to_undeclared) {
          delete ref;
        } else {
          std::ostringstream oss;
          oss << "Invalid type '" << ref->type()
              << "' in reference '" << data::MakeRefKey(*ref) << "'";
          auto error = db->mutable_error()->Add();
          error->set_lineno(obj.lineno());
          error->set_error_message(oss.str());

          // We don't know how to handle this type further; save and skip.
          obj.mutable_unresolved_refs()->AddAllocated(ref);
        }
        continue;
      }

      switch (type_iter->second->flavor()) {
        case proto::TypeFlavor::STRICT: {
          // Handle references to strict types.
          const auto refkey = data::MakeRefKey(*ref);
          auto iter = object_map.find(refkey);
          if (iter == object_map.end()) {
            std::ostringstream oss;
            oss << "Invalid reference to strict type '" << refkey << "'";
            auto error = db->mutable_error()->Add();
            error->set_lineno(obj.lineno());
            error->set_error_message(oss.str());
            obj.mutable_unresolved_refs()->AddAllocated(ref);
          } else {
            // Move the reference to 'refs'.
            obj.mutable_refs()->AddAllocated(ref);
          }
        } break;

        case proto::TypeFlavor::LAZY: {
          // Handle references to lazy types.
          const auto refkey = data::MakeRefKey(*ref);
          auto pair = object_map.insert({refkey, nullptr});
          if (pair.second) {
            // The referenced refkey did not exist; create it.
            proto::Object* objto = db->mutable_object()->Add();
            pair.first->second = objto;
            objto->mutable_id()->CopyFrom(*ref);
            objto->set_lineno(0);
          }
          obj.mutable_refs()->AddAllocated(ref);
        } break;

        case proto::TypeFlavor::IGNORE: {
          // Handle references to ignored types.
          // Get rid of the ref and don't create anything.
          // It was just a word.
          delete ref;
          break;
        }
      }
    }
  }

  // TODO(blais): Warn on types which aren't used.

  // Add errors.
  if (!errors.empty()) {
    // TODO(blais): Can this not be added in a single shot?
    auto* muterrors = db->mutable_error();
    for (auto error : errors) {
      muterrors->AddAllocated(error); // Ownership transfer.
    }
  }

  return absl::OkStatus();
}

}  //  namespace oblique
