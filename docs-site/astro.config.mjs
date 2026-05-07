import abstractData from '@abstractdata/starlight-theme';
import starlight from '@astrojs/starlight';
import { defineConfig } from 'astro/config';

/** Deploy base path for GitHub Pages project sites: e.g. `ASTRO_BASE=/jre-vidget/ bun run build` */
const site = process.env.ASTRO_SITE ?? 'https://jreakin.github.io';
const base = process.env.ASTRO_BASE ?? '/';

export default defineConfig({
	site,
	base,
	integrations: [
		starlight({
			title: 'jre-vidget',
			description:
				'CLI video downloader built on yt-dlp — local replacement for iTube Studio.',
			sidebar: [
				{
					label: 'Documentation',
					items: [
						{ label: 'Overview', link: '/' },
						{ label: 'Setup', link: '/setup/' },
						{ label: 'CLI overview', link: '/reference/cli/' },
					],
				},
				{
					label: 'Guides',
					items: [
						{
							label: 'Download & formats',
							link: '/guides/download/',
						},
						{
							label: 'Architecture',
							link: '/guides/architecture/',
						},
					],
				},
				{
					label: 'API Reference',
					autogenerate: { directory: 'api' },
				},
			],
			social: [
				{
					icon: 'github',
					label: 'GitHub',
					href: 'https://github.com/jreakin/jre-vidget',
				},
			],
			editLink: {
				baseUrl:
					'https://github.com/jreakin/jre-vidget/edit/main/docs-site/src/content/docs',
			},
			plugins: [
				abstractData({
					motion: 'calm',
					credit: 'auto',
					version: 'v0.1.5',
				}),
			],
		}),
	],
});
