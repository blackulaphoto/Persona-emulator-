const fs = require('fs');
const path = require('path');

const layoutPath = path.join(__dirname, '..', 'frontend', '.next', 'static', 'chunks', 'app', 'layout.js');
if (!fs.existsSync(layoutPath)) {
  console.error('layout.js not found:', layoutPath);
  process.exit(1);
}
const content = fs.readFileSync(layoutPath, 'utf8');
const marker = 'sourceMappingURL=data:application/json;charset=utf-8;base64,';
const idx = content.lastIndexOf(marker);
if (idx === -1) {
  console.error('sourceMappingURL marker not found in layout.js');
  process.exit(1);
}
const b64 = content.slice(idx + marker.length).trim();
let json;
try {
  const decoded = Buffer.from(b64, 'base64').toString('utf8');
  json = JSON.parse(decoded);
} catch (e) {
  console.error('Failed to decode/parse source map JSON:', e.message);
  process.exit(1);
}

const sources = json.sources || [];
const sourcesContent = json.sourcesContent || [];
console.log('Found', sources.length, 'sources in sourceMap');

let problemFound = false;
for (let i = 0; i < sources.length; i++) {
  const src = sources[i];
  const sc = sourcesContent[i] || '';
  // Look for unescaped newline inside a single- or double-quoted string literal
  // This is a heuristic: find quotes then a newline before the matching quote
  const regex = /(['"])(?:\\.|(?!\1).)*\n(?:.|)*?\1/s;
  if (regex.test(sc)) {
    console.log('\nPotential multiline literal (unescaped newline) in source:', src);
    const match = sc.match(regex);
    console.log('Match snippet:\n', (match && match[0].slice(0, 400)) || sc.slice(0,200));
    problemFound = true;
  }
  // Also look for bare </script> occurrences
  if (sc.includes('</script>')) {
    console.log('\nFound </script> in source:', src);
    problemFound = true;
  }
}

if (!problemFound) console.log('No obvious multiline string literals or </script> found in embedded sources.');
process.exit(problemFound ? 0 : 0);
