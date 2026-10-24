# Aggrey frontend

The landing page (roadmap module M8): explains Aggrey, shows example questions, and opens Messages to Aggrey's number. Next.js 16 with TypeScript (strict), the App Router, and pnpm. Deployed on Vercel.

## Structure

```text
src/
  app/          layout, page, and global styles
  components/   UI pieces (TextAggreyLink: the "Text Aggrey" sms: link and visible number)
  content/      on-page copy that must match approved docs (sample questions)
  lib/          config (phone number) and helpers (sms link, number formatting)
public/         static files
```

## Configuration

The only setting is `NEXT_PUBLIC_AGGREY_PHONE_NUMBER` (see `.env.example`). Copy `.env.example` to `.env.local` and set it. In `pnpm dev` the page works without it; `pnpm build` fails if it is missing or not in E.164 format. The value is baked into the build, so changing it needs a new deployment.

The page has no database access and no other secrets.

## Commands

Run from `frontend/`:

| Task             | Command                                     |
| ---------------- | ------------------------------------------- |
| Install          | `pnpm install`                              |
| Dev server       | `pnpm dev`                                  |
| Lint             | `pnpm lint`                                 |
| Type check       | `pnpm typecheck`                            |
| Format           | `pnpm format` (CI runs `pnpm format:check`) |
| Production build | `pnpm build`                                |
