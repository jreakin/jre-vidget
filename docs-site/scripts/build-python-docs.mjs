#!/usr/bin/env node
/**
 * build-python-docs.mjs
 *
 * Orchestrates Python autodoc generation for this Starlight site.
 *
 * Reads `scripts/python-autodoc.json`:
 *   - searchPath: relative to docs-site/ — directory on PYTHONPATH (parent of `jre_vidget`)
 *   - modules:    fully-qualified module names
 *   - outputDir:  under docs-site/ (default src/content/docs/api)
 *
 * Runs `uv run pydoc-markdown` from the repo root when `uv.lock` exists; otherwise `pydoc-markdown` on PATH.
 *
 *   bun run docs:python
 *
 * Requires pydoc-markdown (project dev extra: `uv sync --extra dev`).
 */
import { execFileSync } from 'node:child_process';
import { existsSync, mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import { join, resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const PROJECT_ROOT = resolve(__dirname, '..');
const REPO_ROOT = resolve(PROJECT_ROOT, '..');
const CONFIG_PATH = resolve(__dirname, 'python-autodoc.json');

const c = {
	reset: '\x1b[0m',
	dim: '\x1b[2m',
	cyan: '\x1b[36m',
	gold: '\x1b[33m',
	red: '\x1b[31m',
	green: '\x1b[32m',
};
const log = (...a) => console.log(...a);
const die = (msg) => {
	console.error(`${c.red}error${c.reset} ${msg}`);
	process.exit(1);
};

function pydocMarkdownAvailable() {
	const useUv = existsSync(join(REPO_ROOT, 'uv.lock'));
	try {
		if (useUv) {
			execFileSync('uv', ['run', 'pydoc-markdown', '--version'], {
				cwd: REPO_ROOT,
				stdio: 'ignore',
			});
		} else {
			execFileSync('pydoc-markdown', ['--version'], { stdio: 'ignore' });
		}
		return true;
	} catch {
		return false;
	}
}

function runPydocMarkdown(searchPath, mod) {
	const useUv = existsSync(join(REPO_ROOT, 'uv.lock'));
	const args = ['-I', searchPath, '-m', mod];
	if (useUv) {
		return execFileSync('uv', ['run', 'pydoc-markdown', ...args], {
			cwd: REPO_ROOT,
			encoding: 'utf8',
			maxBuffer: 16 * 1024 * 1024,
		});
	}
	return execFileSync('pydoc-markdown', args, {
		encoding: 'utf8',
		maxBuffer: 16 * 1024 * 1024,
	});

}

// ─── Load config ──────────────────────────────────────────────────────
if (!existsSync(CONFIG_PATH)) die(`Missing config: ${CONFIG_PATH}`);
const cfg = JSON.parse(readFileSync(CONFIG_PATH, 'utf8'));
if (!cfg.searchPath) die('python-autodoc.json: `searchPath` is required.');
if (!Array.isArray(cfg.modules) || cfg.modules.length === 0) {
	die('python-autodoc.json: `modules` must be a non-empty array.');
}

const searchPath = resolve(PROJECT_ROOT, cfg.searchPath);
const outputDir = resolve(PROJECT_ROOT, cfg.outputDir ?? 'src/content/docs/api');

if (!existsSync(searchPath)) {
	die(
		`searchPath does not exist: ${searchPath}\n  Resolved from cfg.searchPath = "${cfg.searchPath}"`,
	);
}

log(`${c.dim}→ checking pydoc-markdown${c.reset}`);
if (!pydocMarkdownAvailable()) {
	die(`pydoc-markdown not available. From the repo root run:
  uv sync --extra dev
Then re-run from docs-site: bun run docs:python`);
}

mkdirSync(outputDir, { recursive: true });
log(
	`${c.dim}→ generating ${cfg.modules.length} module page${cfg.modules.length === 1 ? '' : 's'}${c.reset}`,
);

let generated = 0;

for (const mod of cfg.modules) {
	const safeName = mod.replace(/\./g, '_');
	const outPath = join(outputDir, `${safeName}.md`);

	let markdown;
	try {
		markdown = runPydocMarkdown(searchPath, mod);
	} catch {
		log(`${c.red}  ✗ ${mod}${c.reset}`);
		continue;
	}

	const h1 = markdown.match(/^# (.+?)$/m);
	const title = (h1?.[1] ?? mod).trim().replace(/\\_/g, '_');
	let body = h1 ? markdown.replace(h1[0] + '\n', '') : markdown;
	body = body.replace(/<a id="[^"]*"><\/a>\n?/g, '');
	body = body.replace(
		/:(?:mod|class|func|obj|attr|meth|exc|any|data|const)(?::)?\s*`([^`]+)`/g,
		'`$1`',
	);

	const desc = body.split('\n').find((l) => {
		const t = l.trim();
		if (!t) return false;
		if (/^#{1,6} /.test(t)) return false;
		if (t.startsWith('```')) return false;
		if (t.startsWith('|')) return false;
		if (/^[-*+] /.test(t)) return false;
		if (/^<[^>]+>/.test(t)) return false;
		return true;
	});
	const description = (desc ?? `API reference for \`${mod}\`.`)
		.trim()
		.replace(/`/g, '')
		.replace(/"/g, "'")
		.slice(0, 160);

	const frontmatter = ['---', `title: ${title}`, `description: "${description}"`, '---', ''].join(
		'\n',
	);

	writeFileSync(outPath, frontmatter + body);
	generated += 1;
	log(
		`${c.green}  ✓${c.reset} ${mod} ${c.dim}→ ${outPath.replace(PROJECT_ROOT + '/', '')}${c.reset}`,
	);
}

log('');
if (generated === 0) {
	die('No pages generated. Check modules and searchPath in python-autodoc.json.');
}
log(
	`${c.green}✓${c.reset} Generated ${c.gold}${generated}${c.reset} page${generated === 1 ? '' : 's'} in ${c.cyan}${outputDir.replace(PROJECT_ROOT + '/', '')}${c.reset}/`,
);
