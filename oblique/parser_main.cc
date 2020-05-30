#include "oblique/compile.h"
#include "oblique/data.pb.h"
#include "oblique/parser.h"
#include "oblique/scanner.h"

int main(int argc, char **argv)
{
  using namespace oblique;
  if (argc < 2) {
    return EXIT_FAILURE;
  }

  const std::string filename(argv[1]);
  FILE *file = fopen(filename.c_str(), "r");
  if (file == NULL)
  {
    perror("Cannot open file");
    return EXIT_FAILURE;
  }

  auto db = ParseFile(filename);
  if (!Resolve(db.get(), true).ok()) {
    // TODO(blais): Report the errors.
  }
  db->PrintDebugString();

  return 0;
}
