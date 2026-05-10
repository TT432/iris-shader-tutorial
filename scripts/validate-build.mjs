import fs from 'node:fs';
import path from 'node:path';

const dist = path.join(process.cwd(), 'dist');
const docs = path.join(process.cwd(), 'src', 'content', 'docs');
const htmlFiles = [];
const markdownFiles = [];

function walk(dir, visitor) {
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    const fullPath = path.join(dir, entry.name);
    if (entry.isDirectory()) walk(fullPath, visitor);
    else visitor(fullPath);
  }
}

walk(dist, (file) => {
  if (file.endsWith('.html')) htmlFiles.push(file);
});

walk(docs, (file) => {
  if (file.endsWith('.md')) markdownFiles.push(file);
});

const rootAssetPattern = /(src|href)="\/(images|assets|_astro)\//;
const generatedPages = new Set(htmlFiles.map((file) => path.relative(dist, file).replaceAll(path.sep, '/')));
const missingPages = [];
const sparsePages = [];
const rootAssetPages = [];

for (const file of markdownFiles) {
  const rel = path.relative(docs, file).replaceAll(path.sep, '/').replace(/\.md$/, '');
  const expected = rel === 'index' ? 'index.html' : `${rel}/index.html`;
  if (!generatedPages.has(expected)) missingPages.push(expected);
}

for (const file of htmlFiles) {
  const html = fs.readFileSync(file, 'utf8');
  const rel = path.relative(dist, file).replaceAll(path.sep, '/');

  if (rootAssetPattern.test(html)) rootAssetPages.push(rel);
  if (rel !== '404.html') {
    const paragraphs = (html.match(/<p(\s|>)/g) || []).length;
    const codeBlocks = (html.match(/<pre(\s|>)/g) || []).length;
    const images = (html.match(/<img(\s|>)/g) || []).length;
    if (paragraphs < 3 && codeBlocks < 1 && images < 1) {
      sparsePages.push(`${rel} paragraphs=${paragraphs} pre=${codeBlocks} img=${images}`);
    }
  }
}

if (rootAssetPages.length) {
  console.error('Pages with root-relative asset paths:');
  for (const page of rootAssetPages) console.error(`- ${page}`);
}

if (missingPages.length) {
  console.error('Markdown files without generated pages:');
  for (const page of missingPages) console.error(`- ${page}`);
}

if (sparsePages.length) {
  console.error('Pages with suspiciously sparse content:');
  for (const page of sparsePages) console.error(`- ${page}`);
}

if (rootAssetPages.length || missingPages.length || sparsePages.length) process.exit(1);

console.log(`Validated ${htmlFiles.length} HTML files.`);
