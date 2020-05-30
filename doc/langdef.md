# Oblique Data Language

 > WARNING: THIS DOCUMENT IS NOT ACCURATE. This was written before the
 > implementation to document the idea. It will be updated when the
 > implementation is complete.

Oblique is a simple computer language that allows you to define typed data in a
minimalistic language written in text files.

It was originally designed to make it possible to input todo lists, snippets,
and planning tasks referencing bug tracker tickets and client and project names
all in one place, in a format that is remarkably terse yet typed and general.
The final artifact produced from parsing the language is a graph database of
short definitions.

## Syntax

Each line in a program is read in order. All declarations must be made prior to
being used.

I suggest using the `.oblique` extension for files in the Oblique language.

### Objects and Types

The heart of the system is an **object database**. All objects are typed and
contain an **identifier** and a **content** string. Identifiers must be unique
within each object type, across the entire database (it is an error to define
the same object twice).

The contents of an object may contain any free-form text. Objects are related to
other objects. Relationships between objects are extracts from their contents
string.

### Object References

Objects are defined or referenced by an "object reference." An object reference
consists of a type name, a slash, and a type identifier, with this template:
`<type>/<id>`. For example:

    p/apollo
    d/2020-04-18
    cl/3478923445

Object references appear in two places in the code: at the beginning of an
object definition (to define it), or within the content of an object definition
(to establish a relation to it from the object being defined).

### Declarations

Declarations may be **commands** or **object definitions**. Declarations occur
on a single line of text.

#### Comment Syntax

Any line beginning with `#` is a comment and everything after it is ignored.

#### Commands

Commands begin with one of a fixed set of command keywords, which are all single
words starting with "/" and followed by some arguments. Some examples:

    /type/d A calendar date
    /macro P[0-4] p/\1
    /import other_file.oblique

#### Object Definitions

Object definitions begin with an object reference, and are followed by some
free-form text. Beginning a definition with an object reference always defines
that object, and attaches the text following it on that line to the new object
as its contents. Examples:

    q/q2 Second quarter
    o/embed Had meeting about the embedding for client Zelda.

The last definition defines the `o/embed` object of type `o`, with content `Had
meeting about the embedding for client Zelda`.

##### Relations

Object definitions may contain references to other objects. To link an object to
another object, simply insert a reference to it within the contents text (but
not at the beginning), like this:

      Meeting about resolving b/43785784 in project p/zelda.

This creates a new object of type `i` linking to objects `b/43785784` and
`p/zelda`. In this example, `b` may be a bug tracker ticket type and `p` a
project type.

##### Empty Definitions

Object definitions are not required to include content. The simplest type of
definition is simply a new object reference, which defines the object itself,
for example, this defines an object of type `d` with id `2020-04-18`:

      d/2020-04-18

##### Default Type (Items)

It is possible to define new objects without an object reference. If you simply
input a sentence, you will define a new, unique object of type `i` (which stands
for "Item"), which is the default, implicitly define type. For example:

      This is a new object.

This defines a new "item" with a random identifier as the id. It is equivalent
to

      i/12345678 This is a new object.

where `12345678` is an automatically allocated random identifier.

### Commands
#### Defining Types

All objects are typed. New types may be defined with:

    /type/<typename> <contents>

Types also contains a contents string, usually a human-readable description of
the type. For example:

    /type/q Calendar quarter
    /type/o Objective
    /type/cl Change list
    /type/p Project

Type names are intended to be very short as in the examples above, one, two, or
perhaps three lowercase characters as most. The reason for this is that the type
names are also used to refer to objects within the contents of object
definitions and we aim for the referencing to use minimal amounts of syntax.

#### Lazy Types

Object types are by default strict, which means that every object that is
referenced is required to have been defined somewhere. For example, if one of
your definitions references `p/zelda` (project Zelda) within its contents, there
must be a definition for it elsewhere in the program text.

"Lazy" types relax this constraint, and allow you to reference objects without
explicitly declaring them. Defining lazy types follows a similar syntax as for
regular types:

    /lazytype/<typename> <contents>

All objects of lazy types are automatically defined
when referenced. This is useful, for example, for types representing external
entities, e.g.

    /lazytype/b Bug or ticket (in Bug database)
    /lazytype/g Commit number on Github
    /lazytype/d Calendar date
    /lazytype/u User (part of our LDAP database)

#### Macros

Macros allow you to automatically translate input text into object references.
They are defined as regular expression matches and their replacement:

    /macro <regexp> <replacement>

The replacement strings may contain (and typically do) captures from the regular
expression. Here's a use case: say you want to define a "Priority" type with a
few objects:

    /type/p Priority
    p/0 Urgent
    p/1 Important
    p/2 Planned
    p/3 Maybe/optional

You might want to allow users to simply include `Px` as part of their text in
order to reference the priorities, like this:

    /macro \bP[0-3]\b p/\1
    ...
    o/frob Make sure to clean up the Frobnicator before end of quarter P0

Or usernames for ownership:

    /macro \b([a-z]+)@\b u/\1
    ...
    o/frob Make sure to clean up the Frobnicator before end of quarter P0 (joe@)

#### Rendering

The rendering command is in some sense the opposite of the `macro` command: it
specifies how to render an object reference when produces in HTML reports. For
example, say you wanted to render to a bug tracker ticket to an existing system,
you might do this:

    /render b <a href="http://bug-tracker/\1">\1</a>

The `\1` string is replaced by the identifier. Types will often define pairs of
macro/render to produce the output in a similar format as the input:

    /lazytype/u Usernames
    /macro \b([a-z]+)@\b u/\1
    /render u \1@

#### Import

It is possible to import definitions from other files by using the import
statement:

    /import <filename>

Statements imported from other files are subject to the same inheritance rules
as described elsewhere in this document. For example, you could associate all
objects with a quarter by writing a top-level file that includes per-quarter
files, like this:

    q/q1
      /import team-alpha-q1.txt
      /import team-beta-q1.txt
    q/q2
      /import team-alpha-q2.txt
      /import team-beta-q2.txt

#### Query

TODO: Document this.
Select o, q group by o where q/q2 and f/important


## Inheritance

## TODO
