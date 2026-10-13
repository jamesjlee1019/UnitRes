import { useEffect, useState } from 'react'
import { Link } from 'react-router'
import { api } from '../api.ts'
import { TEAMS, type TeamName } from '../teams.ts'

type Health = {
  api: string
  database: string
  apartments?: number
  detail?: string
}

type Status = 'checking' | 'ok' | 'problem'

/**
 * The setup check. If all three rows have a check mark, your laptop is set up.
 *
 * This page is also the example to copy for loading data from the API:
 * keep the result in state, and fetch it in useEffect when the page opens.
 */
export default function HomePage() {
  const [health, setHealth] = useState<Health | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    api<Health>('/health')
      .then(setHealth)
      .catch((err: Error) => setError(err.message))
  }, [])

  const apiStatus: Status = health ? 'ok' : error ? 'problem' : 'checking'
  const dbStatus: Status =
    health?.database === 'ok' ? 'ok' : health || error ? 'problem' : 'checking'

  let dbDetail = 'Checking…'
  if (dbStatus === 'ok') dbDetail = `Connected, with ${health?.apartments} apartments loaded`
  else if (error) dbDetail = "Can't check until the API is running."
  else if (health) dbDetail = 'The API is up but the database isn\'t answering. Run "docker compose logs db".'

  return (
    <div>
      <p className="font-mono text-xs uppercase tracking-[0.2em] text-brand">Week 1 · everyone</p>
      <h1 className="mt-2 text-4xl font-bold tracking-tight sm:text-5xl">Setup check</h1>
      <p className="mt-3 max-w-2xl text-muted">
        If all three rows have a check mark, the project runs on your laptop. That's everyone's
        first goal.
      </p>

      <ul className="mt-8 divide-y divide-line rounded-md border-2 border-ink bg-paper">
        <StatusRow status="ok" label="Website" detail="Running at localhost:3000 (you're on it)" />
        <StatusRow
          status={apiStatus}
          label="API"
          detail={
            apiStatus === 'problem'
              ? 'Can\'t reach it. Just started? Wait a few seconds and refresh. Otherwise run "docker compose logs api" to see why.'
              : apiStatus === 'ok'
                ? 'Running at localhost:8000'
                : 'Checking…'
          }
        />
        <StatusRow status={dbStatus} label="Database" detail={dbDetail} extra={health?.detail} />
      </ul>

      {apiStatus === 'ok' && dbStatus === 'ok' && (
        <p className="mt-4 font-semibold">You're set up. Find your team below.</p>
      )}

      <h2 className="mt-14 text-2xl font-bold tracking-tight">This week, by team</h2>
      <div className="mt-5 grid gap-4 sm:grid-cols-2">
        {(Object.keys(TEAMS) as TeamName[]).map((name) => (
          <TeamCard key={name} name={name} />
        ))}
      </div>

      <p className="mt-10 text-sm text-muted">
        Every API endpoint is listed, and you can try it, at{' '}
        <a className="font-semibold text-ink underline" href="http://localhost:8000/docs">
          localhost:8000/docs
        </a>
        .
      </p>
    </div>
  )
}

const ICONS: Record<Status, { symbol: string; style: string }> = {
  ok: { symbol: '✓', style: 'bg-emerald-600 text-white' },
  problem: { symbol: '✕', style: 'bg-brand text-white' },
  checking: { symbol: '…', style: 'bg-line text-muted' },
}

function StatusRow(props: { status: Status; label: string; detail: string; extra?: string }) {
  const icon = ICONS[props.status]
  return (
    <li className="flex items-start gap-4 px-5 py-4">
      <span
        className={`mt-0.5 flex size-7 shrink-0 items-center justify-center rounded-full text-sm font-bold ${icon.style}`}
        aria-label={props.status}
      >
        {icon.symbol}
      </span>
      <div className="min-w-0">
        <p className="font-semibold">{props.label}</p>
        <p className="text-sm text-muted">{props.detail}</p>
        {props.extra && <p className="mt-1 font-mono text-xs break-all text-muted">{props.extra}</p>}
      </div>
    </li>
  )
}

function TeamCard({ name }: { name: TeamName }) {
  const { goal, files, page, command } = TEAMS[name]
  return (
    <div className="flex flex-col rounded-md border-2 border-ink bg-paper p-5">
      <p className="font-mono text-xs uppercase tracking-[0.2em] text-brand">{name}</p>
      <p className="mt-2 font-semibold">{goal}</p>
      <p className="mt-4 text-sm text-muted">Start in</p>
      <ul className="mt-1 space-y-0.5 font-mono text-xs break-all">
        {files.map((file) => (
          <li key={file}>{file}</li>
        ))}
      </ul>
      <div className="mt-auto pt-5 text-sm">
        {page && (
          <Link className="font-semibold text-brand hover:text-brand-dark" to={page}>
            Open the page →
          </Link>
        )}
        {command && (
          <code className="block rounded bg-ink px-3 py-2 font-mono text-xs break-all text-cream">
            {command}
          </code>
        )}
      </div>
    </div>
  )
}
