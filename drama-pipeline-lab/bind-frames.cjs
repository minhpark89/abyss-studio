// Adapt the upstream better-sqlite3-style writer to a Python sqlite3 transaction.
// Each parametrized command returned here is executed and read back by contracts.py.
const fs = require('node:fs');
const { bindStoryboardFrameImage } = require(process.argv[2]);
const rows = JSON.parse(fs.readFileSync(0, 'utf8'));
const statements = [];
const db = { prepare(sql) { return { run(...values) { statements.push([sql, values]); } }; } };
for (const row of rows) {
  bindStoryboardFrameImage(db, row.id, 'storyboard_first', null, null, row.first);
  bindStoryboardFrameImage(db, row.id, 'storyboard_last', null, null, row.last);
}
process.stdout.write(JSON.stringify(statements));
