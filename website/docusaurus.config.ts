import {themes as prismThemes} from 'prism-react-renderer';
import type {Config} from '@docusaurus/types';
import type * as Preset from '@docusaurus/preset-classic';

const config: Config = {
  title: 'Claude Auto-Skill',
  tagline: 'Automatically generate Claude Code skills from workflow patterns',
  favicon: 'img/favicon.ico',

  future: {
    v4: true,
  },

  url: 'https://MaTriXy.github.io',
  baseUrl: '/claude-auto-skill/',

  organizationName: 'MaTriXy',
  projectName: 'claude-auto-skill',

  onBrokenLinks: 'throw',

  markdown: {
    hooks: {
      onBrokenMarkdownLinks: 'warn',
    },
  },

  i18n: {
    defaultLocale: 'en',
    locales: ['en'],
  },

  presets: [
    [
      'classic',
      {
        docs: {
          routeBasePath: '/',
          sidebarPath: './sidebars.ts',
          editUrl:
            'https://github.com/MaTriXy/claude-auto-skill/tree/main/website/',
        },
        blog: false,
        pages: false,
        theme: {
          customCss: './src/css/custom.css',
        },
      } satisfies Preset.Options,
    ],
  ],

  themeConfig: {
    colorMode: {
      respectPrefersColorScheme: true,
    },
    navbar: {
      title: 'Claude Auto-Skill',
      items: [
        {
          href: 'https://github.com/MaTriXy/claude-auto-skill',
          label: 'GitHub',
          position: 'right',
        },
      ],
    },
    footer: {
      style: 'dark',
      links: [
        {
          title: 'Docs',
          items: [
            {
              label: 'Getting Started',
              to: '/getting-started/installation',
            },
          ],
        },
        {
          title: 'More',
          items: [
            {
              label: 'GitHub',
              href: 'https://github.com/MaTriXy/claude-auto-skill',
            },
          ],
        },
      ],
      copyright: `Copyright © ${new Date().getFullYear()} Yossi Elkrief (MaTriXy). All rights reserved. Built with Docusaurus.`,
    },
    prism: {
      theme: prismThemes.github,
      darkTheme: prismThemes.dracula,
    },
  } satisfies Preset.ThemeConfig,
};

export default config;
