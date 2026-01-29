import {themes as prismThemes} from 'prism-react-renderer';
import type {Config} from '@docusaurus/types';
import type * as Preset from '@docusaurus/preset-classic';

const config: Config = {
  title: 'Auto-Skill',
  tagline: 'Automatically generate skills for any coding agent from workflow patterns',
  favicon: 'img/favicon.svg',

  future: {
    v4: true,
  },

  url: 'https://MaTriXy.github.io',
  baseUrl: '/auto-skill/',

  organizationName: 'MaTriXy',
  projectName: 'auto-skill',

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
            'https://github.com/MaTriXy/auto-skill/tree/main/website/',
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
      title: 'Auto-Skill',
      logo: {
        alt: 'Auto-Skill Logo',
        src: 'img/favicon.svg',
      },
      items: [
        {
          href: 'https://github.com/MaTriXy/auto-skill',
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
              href: 'https://github.com/MaTriXy/auto-skill',
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
