# LandRecord — Intelligent Land Record Digitization (MVP Frontend)

Frontend-only MVP for a land record digitization system, built with Next.js
(App Router), React, TypeScript, and Tailwind CSS. This covers the normal
user/admin experience for verified land records — dashboard, document
upload, and record search/detail — using mock data. It intentionally does
**not** include the clerk/reviewer workflow, authentication, or a backend.

## Getting started

```bash
npm install
npm run dev
```

Then open http://localhost:3000.

Other scripts:

```bash
npm run build   # production build
npm run start   # run the production build
npm run lint    # ESLint
```

## Routes

| Route            | Description                                                |
| ----------------- | ----------------------------------------------------------- |
| `/`               | Dashboard — summary stats, recent records, recent uploads   |
| `/upload`         | Document upload — drag-and-drop, browse, mock upload flow   |
| `/records`        | Land records list — search, filter, sort, paginate          |
| `/records/[id]`   | Land record detail — official record view                   |

## Project structure

```
app/
  layout.tsx           Root layout, font + global styles
  page.tsx              Dashboard ("/")
  upload/page.tsx        Upload page ("/upload")
  records/page.tsx       Records list ("/records")
  records/[id]/page.tsx  Record detail ("/records/[id]")
  globals.css            Tailwind base + a few global rules

components/
  AppShell.tsx          Layout shell (sidebar + header + content)
  Sidebar.tsx            Responsive sidebar navigation
  Header.tsx              Top navbar with page title + profile area
  StatCard.tsx            Dashboard metric card
  LandRecordTable.tsx    Reusable records table (compact + full variants)
  SearchBar.tsx           Search input
  StatusBadge.tsx         Verification status pill
  UploadDropzone.tsx      Drag-and-drop + browse file picker
  EmptyState.tsx          Empty/no-results state
  icons.tsx                Small inline SVG icon set (no icon library dependency)

lib/
  mockData.ts    All mock land records, recent uploads, and derived
                  state/district lookups. No real data — every name,
                  village, and document is fictional.
  api.ts          Data access layer: getLandRecords, getLandRecordById,
                  getDashboardStats, getRecentUploads, uploadDocument.
                  Each function currently reads from mockData.ts behind an
                  artificial delay. TODO(FastAPI) comments in this file mark
                  exactly where to swap in real `fetch` calls.

types/
  landRecord.ts   Shared TypeScript types (LandRecord, RecordStatus,
                  DashboardStats, RecentUpload).
```

## Connecting the FastAPI backend later

All data flows through `lib/api.ts` — no component ever imports
`lib/mockData.ts` directly for record data (only for building filter
dropdown options). To connect a real backend:

1. Add `NEXT_PUBLIC_API_BASE_URL` to a `.env.local` file.
2. In `lib/api.ts`, replace each function body with a `fetch` call to the
   matching FastAPI endpoint — each function already has a `TODO(FastAPI)`
   comment showing the intended request shape.
3. Component code does not need to change, since it already calls
   `getLandRecords`, `getLandRecordById`, `getDashboardStats`,
   `getRecentUploads`, and `uploadDocument` as if they were async APIs.

## Notes

- All data is fictional/mock and stored in `lib/mockData.ts`.
- No authentication, backend, or database is included by design.
- The clerk/reviewer review workflow is intentionally out of scope for this
  frontend and owned by another workstream.
