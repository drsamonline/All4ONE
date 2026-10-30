# All4one — Complete Tool Catalogue

*403 tools · 16 categories · version 4.0.0 · generated from the live registry by `scripts/catalogue.py` — do not edit by hand.*

Every tool below is a working implementation with its own options and its own page in the app. The **Options** column is the exact set of controls that page shows.

| Category | Tools |
|---|---|
| Files | 42 |
| Archives | 14 |
| Text | 39 |
| Data | 30 |
| Encoding | 27 |
| Images | 26 |
| PDF | 24 |
| Media | 20 |
| Documents | 15 |
| Network | 24 |
| System | 33 |
| Disk | 17 |
| Developer | 23 |
| Security | 16 |
| Numbers | 29 |
| Generators | 24 |


## Files

*Copy, move, rename, compare and inspect files and folders · 42 tools*

| Tool | Command | Options | Needs | Description |
|---|---|---|---|---|
| **Bulk Rename** | `bulk-rename` | `folder` (folder, required), `mode` (choice), `find` (text), `replace` (text), `case` (choice), `recursive` (toggle), `pattern` (text), `apply` (toggle), `confirm` (toggle) | — | Rename many files with a find/replace, regex, numbering or case change — preview first. |
| **Change Extensions** | `bulk-extension` | `folder` (folder, required), `from_ext` (text), `to_ext` (text), `recursive` (toggle), `apply` (toggle) | — | Give every file in a folder the same new extension. |
| **Compare Against Checksum** | `hash-compare` | `path` (file, required), `expected` (text, required), `algorithm` (choice) | — | Check a file against an expected hash and say plainly whether it matches. |
| **Compare Two Files** | `compare-files` | `file_a` (file, required), `file_b` (file, required) | — | Byte-level comparison of two files: identical, or where they first differ. |
| **Compare Two Folders** | `compare-folders` | `folder_a` (folder, required), `folder_b` (folder, required), `by_hash` (toggle) | — | Show which files exist on only one side, and which differ in content. |
| **Copy Files From a List** | `batch-copy-list` | `list_file` (file, required), `destination` (folder), `apply` (toggle) | — | Copy every path listed in a text file into one destination folder. |
| **Copy Folder** | `copy-folder` | `source` (folder, required), `destination` (folder), `on_exists` (choice), `verify` (toggle) | — | Copy a folder tree with overwrite control and a verified byte count. |
| **Delete Files From a List** | `batch-delete-list` | `list_file` (file, required), `apply` (toggle), `confirm` (toggle) | changes data | Delete every path listed in a text file — preview first, then confirm. |
| **Duplicate Finder** | `find-duplicates` | `folder` (folder, required), `min_kb` (number), `recursive` (toggle), `report` (save as) | — | Find identical files by content hash and reclaim the wasted space. |
| **Empty Folder Finder** | `empty-folder-finder` | `folder` (folder, required), `delete` (toggle), `confirm` (toggle) | — | List folders that contain nothing, optionally deleting them. |
| **File Info** | `file-info` | `path` (file, required) | — | Size, type, timestamps, permissions and a SHA-256 fingerprint for one file. |
| **File Type Detector** | `file-type-detect` | `path` (file, required) | — | Identify a file from its magic bytes, not its extension. |
| **File Type Report** | `extension-report` | `folder` (folder, required), `report` (save as) | — | Count files and bytes per extension, biggest offenders first. |
| **Filename Conflict Audit** | `case-conflict-audit` | `folder` (folder, required) | — | Find names that differ only by case or trailing space — breaks on Windows and shares. |
| **Find Files** | `file-search` | `folder` (folder, required), `pattern` (text), `contains` (text), `recursive` (toggle), `max_results` (number) | — | Search a folder by name pattern, size and text content. |
| **Flatten Folder** | `flatten-folder` | `folder` (folder, required), `apply` (toggle), `remove_empty` (toggle) | — | Pull every file from nested subfolders up into one flat folder. |
| **Folder Inventory** | `folder-inventory` | `folder` (folder, required), `hashes` (toggle), `report` (save as, required) | — | A full CSV inventory of a folder: name, size, dates, hashes. |
| **Folder Size** | `folder-size` | `folder` (folder, required), `include_files` (toggle) | — | Total size of a folder, with its biggest immediate children ranked. |
| **Folder Summary Card** | `folder-summary` | `folder` (folder, required) | — | One screen of facts about a folder: counts, sizes, newest file and top types. |
| **Folder Tree** | `tree-view` | `folder` (folder, required), `depth` (number), `sizes` (toggle), `pattern` (text) | — | Print the folder structure as a tree, with optional sizes and a depth limit. |
| **Hidden & System Files** | `hidden-files-report` | `folder` (folder, required) | — | List dotfiles and hidden entries that normal folder views skip. |
| **Join File Parts** | `join-files` | `first_part` (file, required), `output` (save as, required) | — | Reassemble a file that was split into numbered parts. |
| **Largest Files** | `disk-hog-files` | `folder` (folder, required), `min_mb` (number), `limit` (number) | — | The biggest files under a folder, largest first — where the space went. |
| **Long Path Audit** | `long-path-audit` | `folder` (folder, required), `limit_chars` (number) | — | Find paths longer than 260 characters, which Windows tools silently fail on. |
| **Move Files** | `move-files` | `files` (files, required), `destination` (folder), `apply` (toggle) | — | Move a set of files into one destination folder, keeping their names. |
| **Number Files in Order** | `sequence-renamer` | `folder` (folder, required), `prefix` (text), `start` (number), `digits` (number), `sort_by` (choice), `apply` (toggle) | — | Number files 001, 002, … in sorted order, keeping the original name. |
| **Path Inspector** | `path-inspect` | `path` (text) | — | Break a path into its parts and show the resolved absolute location. |
| **Permissions Report** | `permissions-report` | `folder` (folder, required), `limit` (number) | — | Show the read/write/execute bits for everything in a folder. |
| **Read-Only Toggle** | `readonly-toggle` | `folder` (folder, required), `pattern` (text), `action` (choice), `recursive` (toggle) | — | Make files read-only, or clear read-only so they can be edited again. |
| **Recently Changed Files** | `recent-files` | `folder` (folder, required), `hours` (number), `limit` (number) | — | Files modified within the last N hours or days, newest first. |
| **Rename by Date** | `rename-by-date` | `folder` (folder, required), `format` (choice), `pattern` (text), `apply` (toggle) | — | Prefix each file with its modified date, so folders sort chronologically. |
| **Rename From a CSV List** | `batch-rename-from-csv` | `folder` (folder, required), `csv_file` (file, required), `apply` (toggle) | — | Rename files using a two-column CSV of old name and new name. |
| **Safe Filename Cleaner** | `safe-filename` | `folder` (folder, required), `apply` (toggle), `spaces` (choice) | — | Turn messy names into clean, cross-platform-safe filenames. |
| **Same Name, Different Content** | `same-name-different` | `folder` (folder, required) | — | Files sharing a name across folders but holding different content. |
| **Set File Timestamps** | `touch-file` | `path` (file, required), `modified` (text), `apply` (toggle) | — | Rewrite a file's created/modified dates — handy for sorting and tests. |
| **Similar Filenames** | `file-twin-finder` | `folder` (folder, required), `threshold` (number) | — | Near-duplicate filenames such as report.pdf, report (1).pdf and report-final.pdf. |
| **Sort Into Month Folders** | `organise-by-month` | `folder` (folder, required), `pattern` (text), `apply` (toggle) | — | File photos and documents into Year/Month folders by their modified date. |
| **Sort Into Type Folders** | `organise-by-type` | `folder` (folder, required), `apply` (toggle), `min_files` (number) | — | Move files into subfolders named after their extension. |
| **Split File** | `split-file` | `path` (file, required), `size_mb` (number), `output` (folder) | — | Cut a large file into numbered chunks of a fixed size. |
| **Verified Copy** | `copy-with-verify` | `files` (files, required), `destination` (folder) | — | Copy files and confirm each one with a SHA-256 comparison. |
| **Verify a Backup** | `backup-verify` | `source` (folder, required), `backup` (folder, required), `by_hash` (toggle) | — | Compare a source folder against its backup by hash and list what is missing. |
| **Zero-Byte File Cleaner** | `delete-empty-files` | `folder` (folder, required), `delete` (toggle), `confirm` (toggle) | — | Find files with nothing in them, optionally deleting them. |


## Archives

*Zip, tar and 7-Zip archives · 14 tools*

| Tool | Command | Options | Needs | Description |
|---|---|---|---|---|
| **7-Zip (Extract / Create)** | `sevenzip` | `archive` (file), `folder` (folder), `destination` (folder), `action` (choice), `password` (text) | 7z | Handle 7z, RAR and other formats through 7-Zip if it is installed. |
| **Add Files to ZIP** | `zip-add` | `archive` (file, required), `folder` (folder), `prefix` (text) | — | Append files or a folder to an existing ZIP without rebuilding it. |
| **Archive Report** | `archive-report` | `archive` (file, required), `report` (save as, required) | — | CSV listing of every entry in an archive, with sizes and compression ratio. |
| **Bzip2 / Bunzip2** | `bzip2-file` | `path` (file, required), `action` (choice) | — | Compress a file with bzip2, or expand a .bz2 archive. |
| **Create TAR** | `tar-create` | `folder` (folder, required), `output` (save as, required), `format` (choice) | — | Pack a folder into a tar, tar.gz or tar.bz2 archive. |
| **Create ZIP** | `zip-create` | `folder` (folder), `output` (save as, required), `level` (number), `include_hidden` (toggle) | — | Zip a folder or a set of files, with a compression level you choose. |
| **Extract TAR** | `tar-extract` | `archive` (file, required), `destination` (folder) | — | Unpack a tar, tar.gz or tar.bz2 archive, safely. |
| **Extract ZIP** | `zip-extract` | `archive` (file, required), `destination` (folder), `overwrite` (toggle) | — | Unpack a ZIP safely — refuses entries that try to escape the folder. |
| **Gzip / Gunzip** | `gzip-file` | `path` (file, required), `action` (choice) | — | Compress one file to .gz, or expand a .gz back to its original. |
| **List Archive Contents** | `archive-list` | `archive` (file, required), `sizes` (toggle) | — | Show every file inside a ZIP or TAR without extracting it. |
| **Remove From ZIP** | `zip-remove` | `archive` (file, required), `pattern` (text, required), `apply` (toggle) | — | Delete matching entries from a ZIP, rewriting it without them. |
| **Split ZIP by Size** | `zip-split` | `folder` (folder, required), `part_mb` (number), `output` (folder) | — | Create several smaller ZIPs so each one fits a size limit (email, uploads). |
| **Test Archive Integrity** | `archive-test` | `archive` (file, required) | — | Verify every entry in a ZIP reads back correctly and report corruption. |
| **Zip Every Subfolder** | `batch-zip-folders` | `folder` (folder, required), `output` (folder), `level` (number) | — | Give each subfolder its own ZIP — one archive per project or album. |


## Text

*Transform, analyse and clean text · 39 tools*

| Tool | Command | Options | Needs | Description |
|---|---|---|---|---|
| **Add Line Numbers** | `add-line-numbers` | `text` (multiline), `file` (file), `output` (save as), `start` (number), `separator` (text), `pad` (number) | — | Prefix every line with a number, with a separator and start value you pick. |
| **Change Case** | `case-convert` | `text` (multiline), `file` (file), `output` (save as), `mode` (choice) | — | UPPER, lower, Title, Sentence, camelCase, snake_case, kebab-case or tOGGLE. |
| **Change Case Across Files** | `batch-case-files` | `folder` (folder, required), `pattern` (text), `mode` (choice), `recursive` (toggle), `apply` (toggle) | — | Apply a case change to the contents of every matching file in a folder. |
| **Convert Encodings in a Folder** | `batch-encoding` | `folder` (folder, required), `pattern` (text), `target` (choice), `recursive` (toggle), `apply` (toggle) | — | Re-save every text file in a folder as UTF-8 (or another encoding). |
| **Convert Line Endings** | `line-endings` | `file` (file, required), `target` (choice), `apply` (toggle) | — | Switch a file between Windows (CRLF), Unix (LF) and old Mac (CR) endings. |
| **Convert Text Encoding** | `encoding-convert` | `file` (file, required), `target` (choice), `output` (save as), `overwrite` (toggle) | — | Re-save a text file in UTF-8, UTF-16, Windows-1252 or Latin-1. |
| **CSV to Markdown Table** | `csv-to-markdown` | `file` (file, required), `delimiter` (text), `align_numbers` (toggle), `output` (save as) | — | Turn CSV into a clean Markdown table ready to paste into notes or a README. |
| **Extract Email Addresses** | `extract-emails` | `text` (multiline), `file` (file), `output` (save as), `sort` (toggle) | — | Pull every email address out of text, de-duplicated and sorted. |
| **Extract Links** | `extract-urls` | `text` (multiline), `file` (file), `output` (save as), `domains_only` (toggle) | — | Collect every URL in a text or page, optionally keeping only unique domains. |
| **Extract Numbers** | `extract-numbers` | `text` (multiline), `file` (file), `output` (save as), `sum` (toggle) | — | Grab every number from text — decimals, negatives and thousands separators. |
| **Extract With Regex** | `regex-extract` | `text` (multiline), `file` (file), `pattern` (text, required), `unique` (toggle), `output` (save as) | — | Pull every match of a pattern out of text — emails, IDs, numbers, anything. |
| **Find & Replace** | `find-replace-text` | `text` (multiline), `file` (file), `find` (text, required), `replace` (text), `case_sensitive` (toggle), `whole_word` (toggle), `regex` (toggle), `output` (save as) | — | Replace text with optional whole-word, case-sensitive and regex modes. |
| **Fix Line Endings in a Folder** | `batch-line-endings` | `folder` (folder, required), `pattern` (text), `target` (choice), `recursive` (toggle), `apply` (toggle) | — | Convert every text file in a folder to one line-ending style. |
| **Fix Smart Quotes & Dashes** | `fix-smart-quotes` | `text` (multiline), `file` (file), `output` (save as) | — | Convert curly quotes, en dashes and ellipses into plain ASCII characters. |
| **HTML to Text** | `strip-html` | `text` (multiline), `file` (file), `links` (toggle), `keep_breaks` (toggle), `output` (save as) | — | Turn HTML into readable plain text, keeping or dropping link addresses. |
| **Join Lines** | `join-lines` | `text` (multiline), `file` (file), `output` (save as), `per_line` (number), `keep_paragraphs` (toggle) | — | Merge every line into one paragraph, or into lines of N words. |
| **Keyword Density** | `keyword-density` | `text` (multiline), `file` (file), `output` (save as), `phrase_words` (number) | — | How often each phrase appears as a share of the text — SEO-style analysis. |
| **Longest Lines** | `longest-lines` | `text` (multiline), `file` (file), `output` (save as), `limit` (number) | — | The longest lines in a text — useful for finding runaway paragraphs. |
| **Make URL Slug** | `slugify-text` | `text` (multiline), `file` (file), `output` (save as), `separator` (choice), `ascii` (toggle) | — | Turn any title into a lowercase, hyphenated, ASCII-only slug. |
| **Markdown to Text** | `markdown-to-text` | `text` (multiline), `file` (file), `output` (save as) | — | Strip Markdown syntax down to clean prose for pasting anywhere. |
| **Readability Statistics** | `text-statistics` | `text` (multiline), `file` (file), `output` (save as) | — | Average word and sentence length plus a Flesch reading-ease score. |
| **Regex Replace** | `regex-replace` | `text` (multiline), `file` (file), `pattern` (text, required), `replacement` (text), `multiline` (toggle), `dotall` (toggle), `output` (save as) | — | Substitute with a full regular expression, including capture groups. |
| **Remove Accents** | `remove-accents` | `text` (multiline), `file` (file), `output` (save as) | — | Normalise accented letters to plain ASCII while keeping the text readable. |
| **Remove Blank Lines** | `remove-blank-lines` | `text` (multiline), `file` (file), `output` (save as), `collapse` (toggle) | — | Delete empty and whitespace-only lines, optionally collapsing runs of them. |
| **Remove Duplicate Lines** | `dedupe-lines` | `text` (multiline), `file` (file), `output` (save as), `ignore_case` (toggle), `keep_last` (toggle) | — | Keep the first occurrence of every line and drop the repeats. |
| **Remove Repeated Words** | `remove-duplicate-words` | `text` (multiline), `file` (file), `output` (save as) | — | Collapse accidental repeats like 'the the' into a single word. |
| **Replace Across Files** | `batch-replace` | `folder` (folder, required), `pattern` (text), `find` (text, required), `replace` (text), `regex` (toggle), `case_sensitive` (toggle), `recursive` (toggle), `apply` (toggle) | — | Find and replace inside every matching file in a folder, with a preview. |
| **Reverse Line Order** | `reverse-lines` | `text` (multiline), `file` (file), `output` (save as), `what` (choice) | — | Flip the order of lines, or reverse the characters in each line. |
| **Sort Lines** | `sort-lines` | `text` (multiline), `file` (file), `output` (save as), `order` (choice), `unique` (toggle) | — | Sort lines alphabetically, numerically, by length or in reverse. |
| **Split Into Sentences** | `split-sentences` | `text` (multiline), `file` (file), `output` (save as) | — | One sentence per line, ready for subtitles, cards or review. |
| **Split Text Into Files** | `split-text-by-lines` | `file` (file, required), `lines` (number), `output` (folder) | — | Cut a long text file into several smaller files of N lines each. |
| **Strip Colour Codes** | `strip-ansi` | `text` (multiline), `file` (file), `output` (save as) | — | Remove ANSI escape sequences from logs and terminal output. |
| **Tabs ↔ Spaces** | `tab-to-spaces` | `text` (multiline), `file` (file), `output` (save as), `direction` (choice), `width` (number) | — | Convert leading tabs to spaces or spaces to tabs at a width you choose. |
| **Text Similarity** | `text-similarity` | `text_a` (multiline), `text_b` (multiline) | — | How alike two texts are, with the longest matching runs highlighted. |
| **Text Summary** | `summarise-text` | `text` (multiline), `file` (file), `output` (save as), `sentences` (number) | — | Pick the most representative sentences to make a quick extractive summary. |
| **Trim Whitespace** | `trim-lines` | `text` (multiline), `file` (file), `output` (save as), `where` (choice), `blank_runs` (toggle) | — | Strip trailing spaces, leading spaces, or both, from every line. |
| **Word Count** | `word-count` | `text` (multiline), `file` (file), `output` (save as) | — | Words, characters, lines, sentences and reading time for any text or file. |
| **Word Frequency** | `word-frequency` | `text` (multiline), `file` (file), `output` (save as), `limit` (number), `min_length` (number), `ignore_common` (toggle) | — | The words used most often, with counts and share of the whole text. |
| **Wrap Text** | `wrap-text` | `text` (multiline), `file` (file), `output` (save as), `width` (number), `keep_indent` (toggle) | — | Re-wrap paragraphs at a fixed column width, preserving paragraph breaks. |


## Data

*JSON, CSV, XML, YAML and SQLite · 30 tools*

| Tool | Command | Options | Needs | Description |
|---|---|---|---|---|
| **Change Delimiter** | `delimiter-convert` | `file` (file, required), `from_delim` (choice), `to_delim` (choice), `quote_all` (toggle), `output` (save as, required) | — | Convert between CSV, TSV, semicolon and pipe-separated files. |
| **Compare JSON** | `json-diff` | `file_a` (file, required), `file_b` (file, required) | — | Show which keys were added, removed or changed between two JSON documents. |
| **Compare Two CSVs** | `csv-compare` | `first` (file, required), `second` (file, required), `key` (text), `report` (save as) | — | Row-level differences between two CSVs, keyed on a column you choose. |
| **Convert Many JSON Files to CSV** | `batch-json-to-csv` | `folder` (folder, required), `output` (folder) | — | Turn every JSON file in a folder into a CSV, one output per input. |
| **CSV Column Report** | `csv-info` | `file` (file, required), `delimiter` (text), `report` (save as) | — | Per column: type, blanks, distinct values, min, max and mean. |
| **CSV to SQLite** | `csv-to-sqlite` | `files` (files, required), `output` (save as, required), `replace` (toggle) | — | Load one or more CSVs into a SQLite database, one table per file. |
| **Extract JSON Path** | `json-extract` | `text` (multiline), `file` (file), `path` (text, required), `output` (save as) | — | Pull one value out of nested JSON with a dotted path like data.users.0.name. |
| **Filter & Sort CSV** | `csv-query` | `file` (file, required), `column` (text), `operator` (choice), `value` (text), `sort_by` (text), `descending` (toggle), `keep` (text), `limit` (number), `output` (save as, required) | — | Filter rows by a condition, sort by any column and keep only the columns you want. |
| **Format JSON** | `json-format` | `text` (multiline), `file` (file), `mode` (choice), `indent` (number), `sort_keys` (toggle), `output` (save as) | — | Pretty-print or minify JSON, with sorted keys and a chosen indent. |
| **Format XML** | `xml-format` | `file` (file, required), `indent` (number), `output` (save as) | — | Indent XML so it can be read, or collapse it to a single line. |
| **INI / Config File Tool** | `ini-tool` | `file` (file, required), `action` (choice), `section` (text), `key` (text), `value` (text), `apply` (toggle) | — | Read, list or rewrite keys in an INI file, keeping other sections intact. |
| **JSON Lines ↔ JSON** | `ndjson` | `file` (file, required), `direction` (choice), `output` (save as, required) | — | Convert between newline-delimited JSON (JSONL) and a JSON array. |
| **JSON to CSV** | `json-to-csv` | `file` (file, required), `output` (save as, required), `delimiter` (text), `limit` (number) | — | Flatten an array of JSON objects into a CSV table, one row per record. |
| **JSON to SQLite** | `json-to-sqlite` | `file` (file, required), `table` (text), `output` (save as, required) | — | Load an array of JSON objects into a SQLite table. |
| **JSON to XML** | `json-to-xml` | `file` (file, required), `root` (text), `output` (save as, required) | — | Render a JSON document as XML with a root element you name. |
| **Merge CSV Files** | `csv-merge` | `files` (files, required), `output` (save as, required), `add_source` (toggle) | — | Stack several CSVs into one, aligning columns by header name. |
| **Merge JSON Files** | `json-merge` | `files` (files, required), `mode` (choice), `output` (save as, required) | — | Combine several JSON files into one array, or deep-merge objects. |
| **Preview CSV** | `csv-preview` | `file` (file, required), `rows` (number), `delimiter` (text) | — | Show a CSV's columns, row count and first rows without opening Excel. |
| **Remove Duplicate Rows** | `csv-dedupe` | `file` (file, required), `columns` (text), `output` (save as, required) | — | Drop repeated rows, either on every column or on the ones you choose. |
| **Run SQL Query** | `sqlite-query` | `file` (file, required), `sql` (multiline), `limit` (number), `output` (save as) | — | Run a read-only SELECT against a SQLite file and save or show the result. |
| **Select / Rename Columns** | `csv-columns` | `file` (file, required), `keep` (text), `drop` (text), `rename` (text), `output` (save as, required) | — | Keep or drop columns and rename headers in one pass. |
| **Sort CSV** | `csv-sort` | `file` (file, required), `columns` (text, required), `descending` (toggle), `output` (save as, required) | — | Sort a CSV by one or more columns, treating numbers as numbers. |
| **Split CSV by Rows** | `csv-split` | `file` (file, required), `rows` (number), `output` (folder) | — | Cut a large CSV into several smaller files of N rows each. |
| **SQLite Table to CSV** | `sqlite-to-csv` | `file` (file, required), `table` (text, required), `output` (save as, required) | — | Export a whole table from a SQLite database into a CSV file. |
| **SQLite Tables** | `sqlite-tables` | `file` (file, required) | — | List the tables, row counts and columns of a SQLite database. |
| **Validate JSON** | `json-validate` | `text` (multiline), `file` (file) | — | Check JSON syntax and report the exact line and column of any problem. |
| **Validate JSON Shape** | `json-schema-lite` | `file` (file, required), `schema` (multiline) | — | Check a JSON document against a compact schema: required keys, types and lengths. |
| **Validate YAML** | `yaml-validate` | `file` (file, required) | — | Parse a YAML file and report structure or the exact error line. |
| **XML to JSON** | `xml-to-json` | `file` (file, required), `attributes` (toggle), `output` (save as, required) | — | Turn an XML document into JSON, keeping attributes and repeated elements. |
| **YAML to JSON** | `yaml-to-json` | `file` (file, required), `direction` (choice), `output` (save as, required) | pyyaml | Convert a YAML document to JSON, or JSON back to YAML. |


## Encoding

*Base64, hex, URLs, hashes and checksums · 27 tools*

| Tool | Command | Options | Needs | Description |
|---|---|---|---|---|
| **All Checksums at Once** | `hash-all` | `file` (file, required), `output` (save as) | — | Every common hash for one file, in a single pass — for release notes. |
| **Ascii85 Encode / Decode** | `ascii85-codec` | `text` (multiline), `action` (choice) | — | Compact text-safe binary encoding, as used inside PDF files. |
| **Base32 Encode / Decode** | `base32-codec` | `text` (multiline), `action` (choice) | — | Base32 is case-insensitive and human-readable — good for codes people retype. |
| **Base64 a File** | `base64-file` | `file` (file, required), `action` (choice), `output` (save as) | — | Encode a file to Base64 text, or rebuild a file from Base64 — for embedding. |
| **Base64 Decode** | `base64-decode` | `text` (multiline), `file` (file), `output` (save as) | — | Turn Base64 back into text, tolerating line breaks and missing padding. |
| **Base64 Encode** | `base64-encode` | `text` (multiline), `file` (file), `wrap` (number), `output` (save as) | — | Encode text or a file to Base64, with optional line wrapping. |
| **Break Down a URL** | `url-parts` | `url` (text, required) | — | Split a URL into scheme, host, port, path, query parameters and fragment. |
| **CRC32 Checksum** | `crc32` | `file` (file), `text` (multiline) | — | The quick 32-bit checksum used to detect accidental file corruption. |
| **Decode a JWT** | `jwt-decode` | `text` (multiline) | — | Read a JSON Web Token's header and payload — signature is shown, not verified. |
| **Escape HTML** | `html-encode` | `text` (multiline), `quotes` (toggle) | — | Escape characters so text displays literally on a web page. |
| **Hash a File** | `hash-file` | `file` (file, required), `algorithm` (choice), `output` (save as) | — | Compute a file's checksum to prove it is the file you think it is. |
| **Hash Every File** | `hash-folder` | `folder` (folder, required), `algorithm` (choice), `report` (save as, required) | — | A CSV of SHA-256 (and friends) for every file in a folder — for manifests. |
| **Hash Text** | `hash-text` | `text` (multiline), `algorithm` (choice), `uppercase` (toggle) | — | Fingerprint a piece of text with any common hash algorithm. |
| **Hex Dump** | `hexdump` | `file` (file, required), `offset` (number), `length` (number), `output` (save as) | — | Classic offset/hex/ASCII view of a file's first bytes — inspect any binary. |
| **Hex to Text** | `hex-decode` | `text` (multiline), `output` (save as) | — | Turn hexadecimal back into readable text, ignoring spaces, colons and 0x. |
| **HMAC Signature** | `hmac-calc` | `text` (multiline), `key` (secret, required), `algorithm` (choice) | — | Sign a message with a secret key — how APIs verify that a request is genuine. |
| **Identify a Hash** | `hash-identify` | `hash` (text, required) | — | Work out which algorithm produced a hash from its length and characters. |
| **International Domains** | `punycode` | `domain` (text, required), `action` (choice) | — | Convert an international domain to punycode (xn--) and back. |
| **Morse Code** | `morse-code` | `text` (multiline), `action` (choice) | — | Translate text to Morse, or Morse back to text. |
| **ROT13 / Caesar Shift** | `rot13` | `text` (multiline), `shift` (number), `alphabet` (choice) | — | Rotate letters by a chosen shift — ROT13 for puzzles, ROT47 for symbols. |
| **Text Fingerprint** | `text-fingerprint` | `text` (multiline), `length` (number) | — | A short, stable ID for a block of text — handy for spotting duplicates. |
| **Text to Binary** | `text-to-binary` | `text` (multiline), `action` (choice) | — | Show text as 8-bit binary, or read binary back into text. |
| **Text to Hex** | `hex-encode` | `text` (multiline), `spaces` (toggle), `prefix` (toggle), `output` (save as) | — | Convert text to hexadecimal bytes, spaced or continuous. |
| **Unescape HTML** | `html-decode` | `text` (multiline) | — | Turn &amp; and &#39; entities back into real characters. |
| **Unicode Escapes** | `unicode-escape` | `text` (multiline), `action` (choice) | — | Convert text to \uXXXX escapes, or turn escapes back into real characters. |
| **URL Decode** | `url-decode` | `text` (multiline), `plus_is_space` (toggle) | — | Turn %20-style escapes back into readable text. |
| **URL Encode** | `url-encode` | `text` (multiline), `mode` (choice) | — | Percent-encode text so it is safe inside a URL or query string. |


## Images

*Resize, convert, watermark and inspect images · 26 tools*

| Tool | Command | Options | Needs | Description |
|---|---|---|---|---|
| **Add a Border** | `image-border` | `file` (file, required), `width` (number), `colour` (colour), `output` (save as) | pillow | Frame an image with a solid border or padding — great for social posts. |
| **Adjust Brightness & Colour** | `image-adjust` | `file` (file, required), `brightness` (number), `contrast` (number), `saturation` (number), `sharpness` (number), `blur` (number), `output` (save as) | pillow | Brighten, darken, add contrast, saturation or blur in one pass. |
| **Apply an Effect** | `image-effect` | `file` (file, required), `effect` (choice), `strength` (number), `output` (save as) | pillow | Grayscale, sepia, invert, pixelate, sketch or posterise an image. |
| **Batch Convert Images** | `image-batch-convert` | `folder` (folder, required), `format` (choice), `quality` (number), `output` (folder), `recursive` (toggle) | pillow | Convert every image in a folder to one format, with a size report. |
| **Batch Resize Images** | `image-batch-resize` | `folder` (folder, required), `max_width` (number), `quality` (number), `output` (folder), `recursive` (toggle) | pillow | Resize a whole folder of images to one maximum size, in one go. |
| **Compare Two Images** | `image-compare` | `first` (file, required), `second` (file, required), `diff_output` (save as) | pillow | How different two images are, as a percentage, with an optional diff image. |
| **Compress a Folder of Images** | `batch-compress-images` | `folder` (folder, required), `quality` (number), `max_width` (number), `output` (folder), `recursive` (toggle) | pillow | Re-encode every image to a smaller file, with a before/after total. |
| **Compress Image** | `image-compress` | `file` (file, required), `quality` (number), `max_width` (number), `output` (save as) | pillow | Shrink a photo's file size by re-encoding at a quality you choose. |
| **Contact Sheet** | `image-contact-sheet` | `folder` (folder, required), `columns` (number), `cell` (number), `background` (colour), `output` (save as, required) | pillow | Tile a folder of images into one overview sheet with captions. |
| **Convert Image Format** | `image-convert` | `file` (file, required), `format` (choice), `quality` (number), `output` (save as) | pillow | Convert between PNG, JPEG, WebP, BMP, TIFF and GIF with a quality setting. |
| **Crop Image** | `image-crop` | `file` (file, required), `mode` (choice), `percent` (number), `left` (number), `top` (number), `right` (number), `bottom` (number), `aspect` (number), `output` (save as) | pillow | Cut an image to a box, a square, or the centre — with exact coordinates if you like. |
| **Dominant Colours** | `image-colours` | `file` (file, required), `count` (number) | pillow | The main colours in an image with their hex codes — for palettes and themes. |
| **Find Duplicate Images** | `duplicate-images` | `folder` (folder, required), `threshold` (number), `report` (save as) | pillow | Spot visually identical images even when they have been resized or re-encoded. |
| **Image Folder Report** | `image-folder-report` | `folder` (folder, required), `report` (save as) | pillow | Count and total the images in a folder by format, with resolution warnings. |
| **Image Info** | `image-info` | `file` (file, required), `exif` (toggle) | pillow | Dimensions, colour mode, DPI, EXIF camera data and file size at a glance. |
| **Join Images** | `image-stitch` | `folder` (folder, required), `direction` (choice), `columns` (number), `gap` (number), `background` (colour), `output` (save as, required) | pillow | Place several images side by side or stacked into one picture. |
| **Make a Windows Icon** | `image-to-ico` | `file` (file, required), `output` (save as, required) | pillow | Turn an image into a multi-size .ico file for apps, folders and shortcuts. |
| **Make Thumbnails** | `image-thumbnails` | `folder` (folder, required), `size` (number), `output` (folder), `format` (choice) | pillow | Square-cropped thumbnails for a whole folder — perfect for cards and galleries. |
| **Remove Image Metadata** | `image-strip-metadata` | `file` (file, required), `output` (save as) | pillow | Strip EXIF, GPS and camera data from photos before sharing them. |
| **Resize Image** | `image-resize` | `file` (file, required), `width` (number), `height` (number), `keep_aspect` (toggle), `resample` (choice), `output` (save as) | pillow | Resize to exact pixels or a percentage, keeping the aspect ratio if you want. |
| **Rotate & Flip** | `image-rotate` | `file` (file, required), `action` (choice), `angle` (number), `expand` (toggle), `output` (save as) | pillow | Rotate by any angle or flip horizontally / vertically, with EXIF auto-correction. |
| **Split Image Into Tiles** | `image-split-tiles` | `file` (file, required), `rows` (number), `columns` (number), `output` (folder) | pillow | Cut an image into a grid of equal tiles — for puzzles, maps and carousels. |
| **Strip Metadata From a Folder** | `batch-strip-exif` | `folder` (folder, required), `output` (folder) | pillow | Remove EXIF, GPS and camera data from every photo in a folder at once. |
| **Thumbnail a Folder Tree** | `batch-thumbnails-folder` | `folder` (folder, required), `size` (number), `output` (folder) | pillow | Make thumbnails for every image under a folder, keeping the folder structure. |
| **Watermark a Folder** | `batch-watermark` | `folder` (folder, required), `text` (text), `position` (choice), `opacity` (number), `output` (folder) | pillow | Stamp the same watermark onto every image in a folder. |
| **Watermark Image** | `image-watermark` | `file` (file, required), `text` (text), `logo` (file), `position` (choice), `opacity` (number), `size` (number), `colour` (colour), `output` (save as) | pillow | Stamp text or a logo onto a photo, with position, opacity, size and colour. |


## PDF

*Merge, split, extract and protect PDFs · 24 tools*

| Tool | Command | Options | Needs | Description |
|---|---|---|---|---|
| **Compare Two PDFs** | `pdf-compare` | `first` (file, required), `second` (file, required), `context` (number) | pypdf | Text differences between two PDFs, page by page — catches re-issued documents. |
| **Compress PDF** | `pdf-compress` | `file` (file, required), `remove_metadata` (toggle), `output` (save as, required) | pypdf | Rewrite a PDF more compactly — strips unused objects and downsamples nothing. |
| **Delete Pages** | `pdf-delete-pages` | `file` (file, required), `pages` (text, required), `output` (save as, required), `password` (secret) | pypdf | Remove pages from a PDF and keep everything else, in the original order. |
| **Edit PDF Metadata** | `pdf-metadata` | `file` (file, required), `title` (text), `author` (text), `subject` (text), `keywords` (text), `clear` (toggle), `output` (save as, required) | pypdf | Set the title, author, subject and keywords, or clear them completely. |
| **Extract Images From PDF** | `pdf-extract-images` | `file` (file, required), `output` (folder) | pypdf | Save every embedded image in a PDF as a picture file. |
| **Extract Pages** | `pdf-extract-pages` | `file` (file, required), `pages` (text, required), `output` (save as, required), `password` (secret) | pypdf | Pull specific pages out of a PDF — '1-3,7,10-' style ranges. |
| **Extract PDF Text** | `pdf-extract-text` | `file` (file, required), `pages` (text), `page_breaks` (toggle), `output` (save as) | pypdf | Pull the text layer out of a PDF, page by page, into a text file. |
| **Extract Text From Many PDFs** | `batch-pdf-text` | `folder` (folder, required), `output_mode` (choice), `output` (folder), `page_marks` (toggle) | pypdf | Turn a folder of PDFs into text files, or one combined text document. |
| **Images to PDF** | `pdf-from-images` | `folder` (folder, required), `output` (save as, required), `sort_by_name` (toggle), `quality` (number) | pillow | Build a PDF from a folder of images, one image per page. |
| **Insert Blank Pages** | `pdf-add-blank` | `file` (file, required), `after_page` (number), `count` (number), `output` (save as, required) | pypdf | Add blank pages at chosen positions — for notes and printing spreads. |
| **Merge Every PDF in a Folder** | `batch-pdf-merge` | `folder` (folder, required), `recursive` (toggle), `output` (save as, required) | pypdf | Combine all PDFs in a folder into one file, in filename order. |
| **Merge PDFs** | `pdf-merge` | `files` (files, required), `output` (save as, required), `bookmarks` (toggle) | pypdf | Combine several PDFs into one, in the order you list them. |
| **Password-Protect PDF** | `pdf-encrypt` | `file` (file, required), `password` (secret, required), `owner_password` (secret), `algorithm` (choice), `output` (save as, required) | pypdf · changes data | Encrypt a PDF with a password so it needs one to open. |
| **PDF Attachments** | `pdf-attachments` | `file` (file, required), `output` (folder), `extract` (toggle) | pypdf | List or extract files embedded inside a PDF. |
| **PDF Bookmarks** | `pdf-bookmarks` | `file` (file, required) | pypdf | Show the document outline, or list every page's text as a flat index. |
| **PDF Form Fields** | `pdf-form-fields` | `file` (file, required), `values` (text), `output` (save as) | pypdf | List a PDF's fillable form fields, or fill them from key=value pairs. |
| **PDF Info** | `pdf-info` | `file` (file, required), `password` (secret) | pypdf | Page count, page sizes, version, metadata and encryption status. |
| **PDF Page Report** | `pdf-page-report` | `file` (file, required), `report` (save as) | pypdf | Per-page size, rotation and text length — spot the odd page in a scan. |
| **PDF Pages to Images** | `pdf-to-images` | `file` (file, required), `dpi` (number), `output` (folder) | pdftoppm | Render each PDF page as a PNG using Poppler's pdftoppm. |
| **Remove PDF Password** | `pdf-decrypt` | `file` (file, required), `password` (secret, required), `output` (save as, required) | pypdf | Save an unlocked copy of a PDF you already have the password for. |
| **Reorder Pages** | `pdf-reorder` | `file` (file, required), `order` (text, required), `reverse` (toggle), `output` (save as, required) | pypdf | Rebuild a PDF in any page order you type — duplicates allowed. |
| **Rotate Pages** | `pdf-rotate` | `file` (file, required), `angle` (choice), `pages` (text), `output` (save as, required) | pypdf | Turn pages 90, 180 or 270 degrees — fixes sideways scans. |
| **Search a PDF** | `pdf-search` | `file` (file, required), `needle` (text, required), `case_sensitive` (toggle) | pypdf | Find a word or phrase and report the pages and lines it appears on. |
| **Split PDF Into Pages** | `pdf-split` | `file` (file, required), `output` (folder), `password` (secret) | pypdf | Save every page of a PDF as its own file. |


## Media

*Audio and video conversion with FFmpeg · 20 tools*

| Tool | Command | Options | Needs | Description |
|---|---|---|---|---|
| **Add Subtitles** | `add-subtitles` | `file` (file, required), `subtitles` (file, required), `mode` (choice), `output` (save as) | ffmpeg | Burn subtitles into the picture, or mux them as a selectable track. |
| **Batch Convert Media** | `media-batch-convert` | `folder` (folder, required), `format` (choice), `output` (folder), `recursive` (toggle) | ffmpeg | Convert every video or audio file in a folder to one format. |
| **Change Playback Speed** | `change-speed` | `file` (file, required), `speed` (number), `keep_pitch` (toggle), `output` (save as) | ffmpeg | Speed up or slow down media while keeping the pitch natural. |
| **Change Volume** | `audio-volume` | `file` (file, required), `mode` (choice), `amount` (number), `output` (save as) | ffmpeg | Boost or quieten audio by a number of decibels or a multiplier. |
| **Compress Video** | `compress-video` | `file` (file, required), `crf` (number), `max_width` (number), `preset` (choice), `output` (save as) | ffmpeg | Make a video smaller by raising CRF or capping the resolution. |
| **Convert Media** | `convert-media` | `file` (file, required), `format` (choice), `quality` (choice), `output` (save as) | ffmpeg | Convert video or audio between formats, choosing codec and quality. |
| **Extract Audio** | `extract-audio` | `file` (file, required), `format` (choice), `bitrate` (number), `output` (save as) | ffmpeg | Pull the sound track out of a video as MP3, WAV, M4A or FLAC. |
| **Extract Video Frames** | `extract-frames` | `file` (file, required), `every_seconds` (number), `output` (folder) | ffmpeg | Save still frames from a video at a fixed interval — for thumbnails or review. |
| **Grab a Thumbnail** | `video-thumbnail` | `file` (file, required), `at` (text), `width` (number), `output` (save as) | ffmpeg | Save one frame from a chosen timestamp as a JPEG or PNG thumbnail. |
| **Images to Video** | `frames-to-video` | `folder` (folder, required), `fps` (number), `output` (save as, required) | ffmpeg | Turn a numbered image sequence into a video at a chosen frame rate. |
| **Join Media Files** | `concat-media` | `files` (files, required), `output` (save as, required) | ffmpeg | Concatenate several audio or video files that share the same format. |
| **Media Info** | `media-info` | `file` (file, required) | ffprobe | Duration, resolution, codecs, frame rate, bitrate and audio tracks. |
| **Normalise Loudness** | `normalise-audio` | `file` (file, required), `target` (number), `output` (save as) | ffmpeg | Even out volume across a recording to a broadcast loudness target. |
| **Remove Audio Track** | `mute-video` | `file` (file, required), `output` (save as) | ffmpeg | Strip the sound from a video entirely, leaving a silent file. |
| **Resize Video** | `resize-video` | `file` (file, required), `width` (number), `height` (number), `output` (save as) | ffmpeg | Scale a video to a new resolution, keeping the aspect ratio. |
| **Rotate Video** | `video-rotate` | `file` (file, required), `angle` (choice), `output` (save as) | ffmpeg | Rotate a video 90, 180 or 270 degrees — fixes phone footage on its side. |
| **Strip Media Metadata** | `media-metadata` | `file` (file, required), `output` (save as) | ffmpeg | Remove titles, GPS tags and device names from a video or audio file. |
| **Trim Media** | `trim-media` | `file` (file, required), `start` (text), `end` (text), `duration` (number), `reencode` (toggle), `output` (save as) | ffmpeg | Cut a section out of a video or audio file by start time and duration. |
| **Trim Silence** | `audio-trim-silence` | `file` (file, required), `threshold` (number), `output` (save as) | ffmpeg | Remove leading and trailing silence from a recording automatically. |
| **Video to GIF** | `video-to-gif` | `file` (file, required), `start` (text), `duration` (number), `width` (number), `fps` (number), `output` (save as) | ffmpeg | Make an animated GIF from a section of a video, with size and frame rate control. |


## Documents

*Word, Excel and document conversion · 15 tools*

| Tool | Command | Options | Needs | Description |
|---|---|---|---|---|
| **Compare Two Word Files** | `docx-compare` | `first` (file, required), `second` (file, required) | docx | Text differences between two .docx files, as a readable diff. |
| **Compare Two Workbooks** | `excel-compare` | `first` (file, required), `second` (file, required), `limit` (number) | openpyxl | Cell-by-cell differences between two Excel files, sheet by sheet. |
| **Convert to PDF** | `office-to-pdf` | `files` (files, required), `output` (folder) | libreoffice | Convert Word, Excel or PowerPoint files to PDF using LibreOffice. |
| **CSV to Excel** | `csv-to-xlsx` | `files` (files, required), `output` (save as, required), `bold_header` (toggle), `autofit` (toggle) | openpyxl | Turn one or more CSV files into a single Excel workbook, one sheet each. |
| **Excel to CSV** | `xlsx-to-csv` | `file` (file, required), `sheet` (text), `output` (folder), `delimiter` (text) | openpyxl | Export a worksheet — or every worksheet — to CSV files. |
| **Excel Workbook Info** | `xlsx-info` | `file` (file, required) | openpyxl | Sheets, used ranges, row counts and whether formulas or macros are present. |
| **Extract Images From Word** | `docx-images` | `file` (file, required), `output` (folder) | docx | Pull every image embedded in a .docx out into a folder. |
| **Merge Excel Workbooks** | `xlsx-merge` | `files` (files, required), `output` (save as, required) | openpyxl | Combine several workbooks into one file, keeping every sheet. |
| **OCR a Scanned PDF** | `ocr-pdf` | `file` (file, required), `language` (text), `dpi` (number), `output` (save as) | tesseract, pdftoppm | Turn a scanned PDF into searchable text, page by page. |
| **OCR an Image** | `ocr-image` | `file` (file, required), `language` (text), `output` (save as) | tesseract | Read the text out of a photo or screenshot with Tesseract. |
| **Search a Workbook** | `xlsx-search` | `file` (file, required), `needle` (text, required), `case_sensitive` (toggle) | openpyxl | Find a value anywhere in an Excel file and report the exact cell. |
| **Text to Word** | `text-to-docx` | `text` (multiline), `file` (file), `title` (text), `output` (save as, required), `markdown` (toggle) | docx | Turn plain text or Markdown-ish text into a formatted .docx. |
| **Word Document Info** | `docx-info` | `file` (file, required) | docx | Paragraph, word, table and image counts plus core properties. |
| **Word Find & Replace** | `docx-find-replace` | `file` (file, required), `find` (text, required), `replace` (text), `apply` (toggle), `output` (save as) | docx | Replace text throughout a .docx, including inside tables. |
| **Word to Text** | `docx-to-text` | `file` (file, required), `tables` (toggle), `output` (save as) | docx | Extract the text of a .docx, keeping paragraph and table order. |


## Network

*Ports, DNS, HTTP, IP maths and diagnostics · 24 tools*

| Tool | Command | Options | Needs | Description |
|---|---|---|---|---|
| **Active Connections** | `netstat-connections` | `listening_only` (toggle) | — | Every current TCP connection and listening port on this machine. |
| **Check a Port** | `port-check` | `host` (text, required), `port` (number), `timeout` (number) | — | Test whether one TCP port on a host is open, and how fast it answers. |
| **Check Many URLs** | `url-status-check` | `urls` (multiline), `timeout` (number), `report` (save as) | — | Test a list of links and report status codes, redirects and response times. |
| **Check TLS Certificate** | `tls-certificate` | `host` (text, required), `port` (number) | — | Issuer, validity dates and days remaining for a site's HTTPS certificate. |
| **Convert an IP Address** | `ip-convert` | `address` (text, required) | — | Show an IPv4 address as decimal, hex, binary, IPv4-mapped IPv6 and reversed form. |
| **DNS Lookup** | `dns-lookup` | `host` (text, required) | — | Resolve a hostname to its addresses, or an address back to its name. |
| **DNS Records** | `dns-records` | `domain` (text, required), `type` (choice) | — | Query MX, TXT, NS, SOA and CNAME records for a domain. |
| **Download a File** | `http-download` | `url` (text, required), `output` (save as, required), `timeout` (number) | — | Download a file with progress, size and a safe resume-free write. |
| **Email Setup Check** | `email-dns-check` | `domain` (text, required) | — | Check a domain's MX, SPF and DMARC records to see if email is set up correctly. |
| **Fetch a URL** | `http-get` | `url` (text, required), `timeout` (number), `max_kb` (number), `output` (save as) | — | Download a page or API response, showing status, headers and the body. |
| **Flush DNS Cache** | `dns-flush` | `confirm` (toggle) | Windows | Clear the resolver cache so a changed DNS record takes effect immediately. |
| **Inspect HTTP Headers** | `http-headers` | `url` (text, required) | — | Check a site's status, security headers and redirect chain without downloading it. |
| **Is an IP in a Subnet?** | `ip-in-subnet` | `address` (text, required), `network` (text, required) | — | Check whether an address belongs to a network, and explain why. |
| **List Every Address in a Range** | `cidr-list` | `cidr` (text, required), `limit` (number), `output` (save as) | — | Print every usable address in a subnet — for inventories and firewall lists. |
| **Local Network Info** | `local-interfaces` | — | — | This machine's name, addresses, gateway and active interface details. |
| **Normalise a MAC Address** | `mac-format` | `mac` (text, required), `style` (choice) | — | Reformat a MAC address into the style a device or router expects. |
| **Ping** | `ping-host` | `host` (text, required), `count` (number), `timeout_ms` (number) | — | Send ICMP pings and report round-trip times, loss and reachability. |
| **Public IP Address** | `public-ip` | `detailed` (toggle) | — | What the internet sees as your address, with country and provider. |
| **Scan Ports** | `port-scan` | `host` (text, required), `ports` (text, required), `timeout` (number), `workers` (number) | — | Check a range of TCP ports on a host you own, and list what is open. |
| **Split a Subnet** | `subnet-split` | `cidr` (text, required), `mode` (choice), `new_prefix` (number), `count` (number) | — | Divide a network into equal smaller subnets, or into a set number of them. |
| **Subnet Calculator** | `ip-calc` | `cidr` (text, required) | — | Everything about a CIDR: mask, network, broadcast, usable host range and count. |
| **Trace Route** | `traceroute` | `host` (text, required), `max_hops` (number) | — | Show the hops a packet takes to reach a host, with timings. |
| **Wake-on-LAN** | `wake-on-lan` | `mac` (text, required), `broadcast` (text), `port` (number) | — | Send a magic packet to wake a sleeping machine on your network. |
| **WHOIS Lookup** | `whois-lookup` | `domain` (text, required) | — | Registration details for a domain, straight from the WHOIS server. |


## System

*Windows settings, processes and startup · 33 tools*

| Tool | Command | Options | Needs | Description |
|---|---|---|---|---|
| **BitLocker Status** | `bitlocker-status` | — | Windows | Drive encryption state for every volume, and whether a key protector exists. |
| **Delete a Registry Value** | `registry-delete` | `hive` (choice), `path` (text, required), `name` (text, required), `confirm` (toggle) | Windows · changes data | Remove one registry value. Export the key first — this cannot be undone. |
| **End a Process** | `process-kill` | `target` (text, required), `confirm` (toggle) | changes data | Stop a process by PID or name — you are asked to confirm the exact target. |
| **Environment Variables** | `env-variables` | `filter` (text), `name` (text) | — | List the environment this app runs with, or look up one variable. |
| **Event Log** | `event-log` | `log` (choice), `level` (choice), `count` (number) | Windows | Recent entries from a Windows event log — errors and warnings by default. |
| **Export a Registry Key** | `registry-export` | `hive` (choice), `path` (text, required), `output` (save as, required) | Windows | Save a registry key to a .reg file before you change anything. |
| **Find a Process** | `process-find` | `name` (text, required) | — | Locate every process with a given name and show its executable path. |
| **Firewall Rules** | `firewall-rules` | `filter` (text), `direction` (choice), `limit` (number) | Windows | Enabled inbound and outbound firewall rules, with ports and programs. |
| **Firewall Status** | `firewall-status` | — | Windows | Whether the Windows firewall is on for each profile. |
| **Hosts File Editor** | `hosts-file` | `action` (choice), `ip` (text), `hostname` (text), `apply` (toggle) | — | Read the hosts file, or add and remove an entry with a backup kept. |
| **Installed Drivers** | `drivers-list` | `filter` (text), `limit` (number) | Windows | Kernel drivers with their state and whether they are signed. |
| **Installed Fonts** | `fonts-list` | `filter` (text) | — | Every font family installed on this machine. |
| **Installed Programs** | `installed-programs` | `filter` (text), `report` (save as) | Windows | Everything installed, with versions and publishers, from the uninstall registry. |
| **Installed Updates** | `windows-updates` | `limit` (number) | Windows | Windows hotfixes and updates installed on this machine. |
| **Local User Accounts** | `users-list` | — | Windows | Accounts on this machine with their enabled state and last logon. |
| **PATH Audit** | `path-audit` | `duplicates_only` (toggle) | — | Check every PATH entry: which exist, which are duplicates and what is missing. |
| **Power Plans** | `power-plans` | — | Windows | Available power plans and which one is active. |
| **Printers** | `printers-list` | — | Windows | Installed printers with their driver, port and default status. |
| **Process List** | `process-list` | `filter` (text), `sort` (choice), `limit` (number) | — | Running processes with PID, memory and CPU — sorted by what is heaviest. |
| **Read the Registry** | `registry-read` | `hive` (choice), `path` (text, required), `value` (text) | Windows | Show the values in a registry key, or one value if you name it. |
| **Scan a Folder With Defender** | `defender-scan` | `folder` (folder, required), `kind` (choice) | Windows | Run a Windows Defender scan on a file or folder and report the result. |
| **Scheduled Tasks** | `scheduled-tasks` | `filter` (text), `ready_only` (toggle) | Windows | Windows scheduled tasks with their state, trigger time and action. |
| **Search the Registry** | `registry-search` | `needle` (text, required), `hive` (choice), `limit` (number) | Windows | Find a word in registry key names under a hive — slow but thorough. |
| **Shut Down / Restart** | `power-actions` | `action` (choice), `delay_seconds` (number), `confirm` (toggle) | Windows · changes data | Lock, sleep, restart or shut down this machine after a delay you choose. |
| **Start / Stop a Service** | `service-control` | `name` (text, required), `action` (choice), `confirm` (toggle) | Windows · changes data | Start, stop or restart a Windows service by name — administrator rights needed. |
| **Startup Programs** | `startup-items` | `details` (toggle) | Windows | Everything that launches at login — registry Run keys and the startup folder. |
| **System Information** | `system-info` | — | — | Operating system, CPU, memory, uptime and Python runtime in one view. |
| **Temp Folder Info** | `temp-path` | — | — | Where temporary files live and how much space they are using. |
| **Uptime** | `uptime` | — | — | How long since the machine last booted, and when that was. |
| **Wi-Fi Networks** | `wifi-networks` | `show` (choice) | Windows | Saved Wi-Fi profiles and the networks currently in range. |
| **Windows Defender Status** | `defender-status` | — | Windows | Antivirus and firewall state, signature age and last scan time. |
| **Windows Services** | `services-list` | `filter` (text), `state` (choice) | Windows | Installed services with their state and start mode, running ones first. |
| **Write a Registry Value** | `registry-write` | `hive` (choice), `path` (text, required), `name` (text, required), `data` (text, required), `type` (choice), `confirm` (toggle) | Windows · changes data | Create or change one registry value. Export the key first — this is permanent. |


## Disk

*Space, drives and large-file hunting · 17 tools*

| Tool | Command | Options | Needs | Description |
|---|---|---|---|---|
| **Biggest Folders** | `big-folders` | `folder` (folder, required), `depth` (number), `top` (number) | — | Rank subfolders by total size at any depth — find the real space hogs. |
| **Clean Temporary Files** | `temp-clean` | `user_temp` (toggle), `windows_temp` (toggle), `preview` (toggle) | changes data | Delete files from the temp folders, skipping anything in use. |
| **Cleanup Opportunities** | `cleanup-report` | `include_downloads` (toggle) | — | Sizes of the usual junk folders — temp, caches, downloads, recycle bin. |
| **Count Files and Folders** | `file-count` | `folder` (folder, required), `pattern` (text) | — | How many files and folders sit under a path, at any depth. |
| **Disk Health (S.M.A.R.T.)** | `disk-health` | — | Windows | Physical disk health, media type and whether SMART predicts a failure. |
| **Disk Space** | `disk-space` | — | — | Every drive with total, used and free space, and how full it is. |
| **Disk Speed Test** | `disk-speed-test` | `folder` (folder), `size_mb` (number) | — | Measure sequential write and read speed on a drive with a temporary file. |
| **Empty Recycle Bin** | `recycle-bin` | `confirm` (toggle) | Windows · changes data | Clear the Windows Recycle Bin and report how much space that frees. |
| **File Age Report** | `file-age-report` | `folder` (folder, required) | — | How many files fall into each age bucket, and how much space they take. |
| **Folder Size Tree** | `folder-size-tree` | `folder` (folder, required), `depth` (number), `top` (number) | — | Recursive sizes for a folder tree — where the space actually goes. |
| **Free Space Check** | `free-space-alert` | `threshold` (number) | — | Flag any drive that is below a percentage you consider safe. |
| **NTFS Alternate Streams** | `ntfs-streams` | `folder` (folder, required) | Windows | Find hidden alternate data streams that can conceal files on NTFS. |
| **Old Files** | `old-files` | `folder` (folder, required), `days` (number), `min_mb` (number), `limit` (number), `report` (save as) | — | Files not modified for a long time — the safest things to archive or delete. |
| **Partitions** | `partition-list` | — | — | Partitions with their sizes, filesystems and drive letters. |
| **Shadow Copies** | `shadow-copies` | — | Windows | Volume shadow copies / restore points available for rollback. |
| **USB Devices** | `usb-devices` | — | Windows | Connected USB devices with their status — spot unknown sticks and gadgets. |
| **Volume Information** | `volume-info` | — | — | Volume labels, filesystems, serial numbers and free space. |


## Developer

*Code, regex, diffs and project checks · 23 tools*

| Tool | Command | Options | Needs | Description |
|---|---|---|---|---|
| **Check a .env File** | `env-file` | `file` (file, required) | — | Parse a .env file, show its keys and flag empty or duplicated values. |
| **Check HTML Structure** | `html-validate` | `file` (file, required) | — | Find unclosed, mismatched and deprecated tags in an HTML file. |
| **Check Python Imports** | `python-import-check` | `file` (file, required) | — | Verify that every import in a Python file can actually be resolved. |
| **Check Python Syntax** | `python-syntax-check` | `folder` (folder), `file` (file) | — | Compile Python files to find syntax errors, with the exact line. |
| **Check requirements.txt** | `requirements-check` | `file` (file, required) | — | Which packages in a requirements file are installed, missing or outdated. |
| **Code Statistics** | `code-stats` | `folder` (folder, required), `skip_hidden` (toggle) | — | Lines of code per language, with blank and comment line counts. |
| **Compare or Bump Versions** | `semver` | `version` (text, required), `action` (choice), `other` (text), `bump` (choice) | — | Compare two semantic versions, or bump one by major, minor or patch. |
| **Compare Text** | `diff-text` | `file_a` (file), `file_b` (file), `text_a` (multiline), `text_b` (multiline), `context` (number) | — | A unified diff between two blocks of text or two files. |
| **Convert Colours** | `colour-convert` | `colour` (colour), `against` (colour) | — | Convert between HEX, RGB, HSL and CMYK, with the WCAG contrast ratio. |
| **Detect File Encoding** | `encoding-detect` | `file` (file, required) | — | Work out whether a file is UTF-8, UTF-16, Windows-1252 or Latin-1, and if it has a BOM. |
| **Explain a Cron Expression** | `cron-explain` | `expression` (text, required) | — | Turn a cron schedule into plain English, with the next few run times. |
| **Format SQL** | `sql-format` | `text` (multiline), `file` (file), `uppercase` (toggle) | — | Put a SQL query back into readable lines with keywords upper-cased. |
| **Git Branches** | `git-branches` | `folder` (folder, required), `merged_only` (toggle) | git | Local and remote branches, with the current one marked. |
| **Git Diff** | `git-diff` | `folder` (folder, required), `staged` (toggle), `stat_only` (toggle) | git | Uncommitted changes in a repository, with a per-file summary. |
| **Git Log** | `git-log` | `folder` (folder, required), `count` (number), `format` (choice) | git | Recent commits with author, date and message, as a table or a changelog. |
| **Git Status** | `git-status` | `folder` (folder, required) | git | Working tree state of a repository: branch, changes and sync position. |
| **Indentation Report** | `indentation-report` | `folder` (folder, required), `pattern` (text), `recursive` (toggle) | — | Tabs or spaces, how wide, and whether a file is internally consistent. |
| **Long Line Report** | `line-length-report` | `folder` (folder, required), `max_length` (number), `pattern` (text), `recursive` (toggle) | — | Files and lines that exceed a width limit — for style clean-up. |
| **Markdown Check** | `markdown-lint` | `file` (file, required) | — | Spot broken links, skipped heading levels, long lines and stray HTML. |
| **Minify CSS / JS / HTML** | `minify` | `file` (file, required), `kind` (choice), `output` (save as, required) | — | Strip comments and whitespace from CSS, JavaScript or HTML to shrink it. |
| **Python File Outline** | `python-outline` | `file` (file, required) | — | Every class and function in a Python file, with line numbers and docstrings. |
| **Regex Tester** | `regex-tester` | `pattern` (text, required), `text` (multiline), `ignore_case` (toggle), `multiline` (toggle), `replacement` (text) | — | Test a regular expression live: matches, groups, positions and replacements. |
| **TODO Scanner** | `todo-scan` | `folder` (folder, required), `tags` (text), `report` (save as) | — | Collect every TODO, FIXME, HACK and XXX comment in a project. |


## Security

*Passwords, encryption and audits · 16 tools*

| Tool | Command | Options | Needs | Description |
|---|---|---|---|---|
| **Constant-Time Compare** | `secure-compare` | `first` (secret, required), `second` (secret, required) | — | Compare two secrets without leaking timing information — for token checks. |
| **Decrypt a File** | `file-decrypt` | `file` (file, required), `password` (secret, required), `output` (save as) | cryptography | Decrypt a file this app encrypted, given the right passphrase. |
| **Derive a Key (PBKDF2)** | `pbkdf2` | `password` (secret, required), `salt` (text), `iterations` (number), `length` (number) | — | Turn a passphrase into a fixed-length key, the way password managers do. |
| **Encrypt a File** | `file-encrypt` | `file` (file, required), `password` (secret, required), `output` (save as) | cryptography | AES-256 encryption with a passphrase — the file is useless without it. |
| **Hash Crack Time** | `crack-time` | `password` (secret, required), `algorithm` (choice) | — | How long an attacker needs to brute-force a password hash, by algorithm. |
| **Measure Entropy** | `entropy` | `file` (file), `text` (multiline) | — | Shannon entropy of a text or file — high values suggest encryption or compression. |
| **Password Strength** | `password-strength` | `password` (secret, required) | — | Entropy, a crack-time estimate and the specific reasons a password is weak. |
| **Scan for Personal Data** | `pii-scan` | `folder` (folder, required), `indian` (toggle) | — | Find emails, phone numbers, card numbers and ID patterns in a folder. |
| **Scan for Secrets** | `secrets-scan` | `folder` (folder, required), `skip_common` (toggle), `report` (save as) | — | Look through a project for API keys, tokens and private keys left in code. |
| **Shred a File** | `file-shred` | `file` (file, required), `passes` (number), `confirm` (toggle) | changes data | Overwrite a file's contents before deleting it, so it cannot be recovered easily. |
| **Shred a Folder** | `folder-shred` | `folder` (folder, required), `preview` (toggle), `confirm` (toggle) | changes data | Overwrite and delete every file in a folder — irreversible, with a preview. |
| **Suspicious Filenames** | `suspicious-names` | `folder` (folder, required) | — | Spot double extensions and disguises like invoice.pdf.exe. |
| **Two-Factor Code (TOTP)** | `totp-generate` | `secret` (secret, required), `digits` (number), `period` (number) | — | Generate the current 6-digit authenticator code from a base32 secret. |
| **Validate a Card Number** | `card-validate` | `number` (text, required) | — | Check a card number's Luhn checksum and identify the network. |
| **Verify a Two-Factor Code** | `totp-verify` | `secret` (secret, required), `code` (text, required), `window` (number) | — | Check whether a 6-digit code is valid for a secret, allowing clock drift. |
| **World-Writable Files** | `world-writable` | `folder` (folder, required) | — | Files anyone on the system can modify — a classic privilege-escalation hole. |


## Numbers

*Dates, times, units and calculations · 29 tools*

| Tool | Command | Options | Needs | Description |
|---|---|---|---|---|
| **Add to a Date** | `date-add` | `start` (text), `days` (number), `weeks` (number), `months` (number), `years` (number) | — | Add or subtract days, weeks, months or years from a date. |
| **Age Calculator** | `age-calc` | `birthdate` (text, required) | — | Exact age in years, months and days, plus the next birthday countdown. |
| **Aspect Ratio Helper** | `aspect-ratio` | `width` (number), `height` (number), `target_width` (number) | — | Reduce a resolution to its aspect ratio, or work out a matching size. |
| **BMI Calculator** | `bmi` | `weight_kg` (number), `height_cm` (number) | — | Body mass index with WHO and Indian cut-offs, plus a healthy weight range. |
| **BMR & Daily Calories** | `bmr-tdee` | `weight_kg` (number), `height_cm` (number), `age` (number), `sex` (choice), `activity` (choice) | — | Resting energy use (Mifflin-St Jeor) and daily calories by activity level. |
| **Compound Interest** | `compound-interest` | `principal` (number), `rate` (number), `years` (number), `frequency` (choice), `monthly_add` (number) | — | Growth of an investment with monthly, quarterly or yearly compounding. |
| **Daily Fluid Requirement** | `fluid-requirement` | `weight_kg` (number), `activity` (choice), `hot_day_c` (number) | — | A maintenance fluid estimate by weight and activity, in litres and glasses. |
| **Data Size Converter** | `bytes-units` | `value` (number), `from_unit` (choice), `speed_mbps` (number) | — | Convert between bytes, KB, MB, GB and TB, and show what a file costs to transfer. |
| **Date Difference** | `date-diff` | `from_date` (text, required), `to_date` (text, required) | — | Days, weeks, months and working days between two dates. |
| **Discount Calculator** | `discount` | `price` (number), `discount` (number), `extra` (number) | — | Sale price, amount saved, and the effective discount between two prices. |
| **Epoch / Timestamp Converter** | `epoch-convert` | `value` (text), `milliseconds` (toggle) | — | Convert between Unix timestamps and readable dates, in your local time and UTC. |
| **Format Indian Currency** | `indian-currency` | `amount` (number), `words` (toggle) | — | Write an amount the Indian way — lakhs, crores and 2,34,567 grouping. |
| **GCD & LCM** | `gcd-lcm` | `numbers` (text, required) | — | Greatest common divisor and least common multiple of a list of numbers. |
| **GST Calculator** | `gst-calc` | `amount` (number), `rate` (choice), `mode` (choice), `supply` (choice) | — | Add or remove GST at any rate, and split CGST/SGST or IGST correctly. |
| **Loan EMI Calculator** | `emi-calc` | `principal` (number), `rate` (number), `years` (number), `months` (number) | — | Monthly EMI, total interest and a year-by-year repayment split. |
| **Number Base Converter** | `base-convert` | `number` (text, required), `from_base` (number), `to_base` (number) | — | Convert a number between binary, octal, decimal, hex and any base up to 36. |
| **Number to Words** | `number-words` | `number` (number) | — | Write a number out in English, using the Indian lakh/crore system. |
| **Percentage Calculator** | `percentage` | `x` (number), `y` (number), `mode` (choice) | — | What is X% of Y, what percent is X of Y, and percent increase or decrease. |
| **Prime Check & Factorise** | `prime` | `number` (number) | — | Test whether a number is prime, and break any number into its prime factors. |
| **Quadratic Solver** | `quadratic` | `a` (number), `b` (number), `c` (number) | — | Roots, vertex and discriminant for ax² + bx + c = 0. |
| **Roman Numerals** | `roman` | `value` (text, required) | — | Convert a number to Roman numerals, or Roman numerals back to a number. |
| **Round Numbers** | `rounding` | `numbers` (text, required), `decimals` (number), `mode` (choice) | — | Round a list of numbers to a chosen precision, or to the nearest 5, 10 or 100. |
| **Simple Interest** | `simple-interest` | `principal` (number), `rate` (number), `years` (number) | — | Straight-line interest on a principal, as used for many loans and deposits. |
| **Simplify a Ratio** | `ratio` | `ratio` (text, required), `total` (number) | — | Reduce a ratio to its simplest form, and split an amount in that ratio. |
| **Statistics** | `statistics` | `numbers` (text, required), `outliers` (toggle) | — | Mean, median, mode, standard deviation, quartiles and outliers for a list. |
| **Temperature Converter** | `temperature-convert` | `value` (number), `from_unit` (choice) | — | Convert between Celsius, Fahrenheit and Kelvin, with fever bands for reference. |
| **Time Zone Converter** | `timezone-convert` | `when` (text), `from_zone` (text), `to_zone` (text) | — | Turn a moment in one time zone into the same moment in another. |
| **Unit Converter** | `unit-convert` | `category` (choice), `value` (number), `from_unit` (text), `to_unit` (text) | — | Convert length, mass, area, volume, speed, data, time, energy or pressure. |
| **Working Days** | `working-days` | `start` (text), `end` (text), `holidays` (text) | — | Count business days in a month or between two dates, skipping weekends. |


## Generators

*IDs, passwords, data and dummy files · 24 tools*

| Tool | Command | Options | Needs | Description |
|---|---|---|---|---|
| **Colour Palette** | `colour-palette` | `colours` (number), `scheme` (choice) | — | A harmonious random palette with hex codes and a contrast check. |
| **Dice Roller** | `dice-roll` | `notation` (text, required), `rolls` (number) | — | Roll dice in standard notation — 2d6, 1d20+3 — with a breakdown. |
| **Dummy CSV** | `dummy-csv` | `rows` (number), `columns` (text), `output` (save as, required) | — | Realistic test data as CSV — names, emails, cities, amounts and dates. |
| **Dummy File** | `dummy-file` | `size_mb` (number), `content` (choice), `output` (save as, required) | — | Create a file of an exact size — for testing uploads, limits and copy speeds. |
| **Dummy JSON** | `dummy-json` | `records` (number), `nested` (toggle), `output` (save as, required) | — | A JSON array of mock records for API stubs and front-end work. |
| **Generate API Keys** | `api-key` | `bytes` (number), `count` (number), `prefix` (text), `encoding` (choice) | — | Random API-style keys, with an optional prefix and hex or base64 form. |
| **Generate OTPs** | `otp-generate` | `digits` (number), `count` (number) | — | One-time codes of a chosen length, with an expiry note for testing flows. |
| **Generate Passphrases** | `passphrase-generate` | `words` (number), `count` (number), `separator` (choice), `capitalise` (toggle), `number` (toggle) | — | Memorable word-based passphrases — long, random and easy to type. |
| **Generate Passwords** | `password-generate` | `length` (number), `count` (number), `lower` (toggle), `upper` (toggle), `digits` (toggle), `symbols` (toggle), `no_ambiguous` (toggle) | — | Strong random passwords with the exact character sets you allow. |
| **Generate PINs** | `pin-generate` | `length` (number), `count` (number), `avoid_patterns` (toggle) | — | Random numeric PINs, avoiding trivial patterns if you want. |
| **Generate UUIDs** | `uuid-generate` | `count` (number), `style` (choice) | — | RFC 4122 version 4 identifiers, formatted the way you need them. |
| **Lorem Ipsum** | `lorem-ipsum` | `unit` (choice), `count` (number), `classic_start` (toggle), `output` (save as) | — | Filler text by words, sentences or paragraphs — for layouts and mockups. |
| **Number Picker** | `lottery-numbers` | `lowest` (number), `highest` (number), `picks` (number), `sorted` (toggle) | — | Unique random numbers for lotteries, draws and sampling without repeats. |
| **Password Batch** | `password-batch` | `count` (number), `length` (number), `output` (save as, required) | — | A CSV of users with generated passwords — for seeding test accounts. |
| **Pick From a List** | `pick-from-list` | `text` (multiline), `winners` (number) | — | Draw one or more winners from a list, without repeating a winner. |
| **Placeholder Image** | `placeholder-image` | `width` (number), `height` (number), `background` (colour), `text_colour` (colour), `label` (text), `output` (save as, required) | pillow | A labelled placeholder image at any size — for mockups and layout tests. |
| **Random Dates** | `random-date` | `start` (text), `end` (text), `count` (number), `format` (choice), `sorted` (toggle) | — | Random dates in a range, formatted the way your system expects. |
| **Random Numbers** | `random-number` | `minimum` (number), `maximum` (number), `count` (number), `integers` (toggle), `unique` (toggle) | — | Random integers or decimals in a range, with or without duplicates. |
| **Random Strings** | `random-string` | `length` (number), `count` (number), `alphabet` (choice) | — | Random text from any character set you choose. |
| **Sample Names & Emails** | `test-names` | `count` (number), `format` (choice) | — | A ready list of realistic Indian names, emails and cities for test data. |
| **Sequential IDs** | `sequential-ids` | `start` (number), `count` (number), `prefix` (text), `padding` (number), `suffix` (text) | — | A clean run of IDs with a prefix, padding and separator — for bulk imports. |
| **Short IDs (NanoID style)** | `nanoid` | `length` (number), `count` (number), `prefix` (text) | — | Compact URL-safe identifiers for records, links and test data. |
| **Shuffle a List** | `shuffle-lines` | `text` (multiline), `file` (file), `number` (toggle) | — | Randomise the order of lines — for draws, assignments and test order. |
| **Split Into Teams** | `team-split` | `text` (multiline), `teams` (number), `number` (toggle) | — | Divide a list of people into balanced random teams. |


## Optional dependencies

| Dependency | Type | Unlocks | Status here |
|---|---|---|---|
| 7-Zip (7z / rar archives) | binary | 1 tools | not installed |
| FFmpeg (audio & video) | binary | 19 tools | not installed |
| ffprobe (media metadata) | binary | 1 tools | not installed |
| Git | binary | 4 tools | present |
| LibreOffice (Office conversion) | binary | 1 tools | present |
| Pandoc (document conversion) | binary | 0 tools | not installed |
| Poppler (pdftoppm — PDF to images) | binary | 2 tools | present |
| Poppler (pdftotext / pdfinfo) | binary | 0 tools | present |
| qpdf (PDF structure repair) | binary | 0 tools | not installed |
| Tesseract (OCR engine) | binary | 2 tools | not installed |
| cryptography (strong encryption) | python | 2 tools | present |
| NumPy (numeric arrays) | python | 0 tools | present |
| openpyxl (Excel files) | python | 6 tools | present |
| Pillow (image library) | python | 28 tools | present |
| psutil (process & system metrics) | python | 0 tools | not installed |
| pypdf (PDF library) | python | 22 tools | present |
| pyperclip (system clipboard) | python | 0 tools | not installed |
| python-docx (Word files) | python | 6 tools | present |
| pywin32 (Windows APIs) | python | 0 tools | not installed |
| PyYAML (YAML parsing) | python | 1 tools | present |
| Send2Trash (recycle bin) | python | 0 tools | not installed |

Nothing in this table is required: the app and 309 tools run on the standard library alone.
