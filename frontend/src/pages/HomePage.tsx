import { useEffect, useState, type FormEvent } from 'react'
import { Link } from 'react-router'
import { api, type ApplicationProfile } from '../api.ts'
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
export default function HomePage({ setupOnly = false }: { setupOnly?: boolean }) {
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

  if (!setupOnly) {
    return <GeneralApplication />
  }

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

function GeneralApplication() {
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [phone, setPhone] = useState('')
  const [moveInDate, setMoveInDate] = useState('')
  const [roommates, setRoommates] = useState<string[]>([])
  const [formError, setFormError] = useState<string | null>(null)

  function submitApplication(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const applicantName = name.trim()
    const roommateNames = roommates.map((roommate) => roommate.trim()).filter(Boolean)
    const names = [applicantName, ...roommateNames]
    const duplicate = names.find((candidate, index) =>
      names.slice(0, index).some((previous) => previous.toLowerCase() === candidate.toLowerCase()),
    )
    if (duplicate) {
      setFormError(`"${duplicate}" is listed more than once. Each person can only be listed once.`)
      return
    }

    const profile: ApplicationProfile = {
      applicantName,
      email: email.trim(),
      phone: phone.trim(),
      moveInDate,
      roommateNames,
    }
    sessionStorage.setItem('unitres.application', JSON.stringify(profile))
    window.location.href = '/apartments'
  }

  return (
    <section>
      <div className="overflow-hidden rounded-lg border-2 border-ink bg-ink px-6 py-8 text-cream sm:px-10">
        <p className="font-mono text-xs uppercase tracking-[0.2em] text-brand">JSM Living</p>
        <h1 className="mt-3 max-w-3xl text-4xl font-bold tracking-tight sm:text-5xl">
          Start your general application.
        </h1>
        <p className="mt-4 max-w-2xl text-cream/70">
          Tell us about everyone who will live with you, then browse JSM&apos;s available portfolio
          by property and building.
        </p>
      </div>

      <form className="mt-8 max-w-2xl space-y-5 rounded-md border-2 border-line bg-paper p-6 sm:p-8" onSubmit={submitApplication}>
        <div>
          <h2 className="text-2xl font-bold">Applicant information</h2>
          <p className="mt-1 text-sm text-muted">Use the same email as your JSM application and security deposit.</p>
        </div>
        <label className="block text-sm font-semibold">
          Full name
          <input className="mt-1 block w-full rounded-md border border-line bg-cream px-3 py-2.5 font-normal" value={name} onChange={(event) => setName(event.target.value)} required maxLength={200} />
        </label>
        <div className="grid gap-5 sm:grid-cols-2">
          <label className="block text-sm font-semibold">
            Email
            <input type="email" className="mt-1 block w-full rounded-md border border-line bg-cream px-3 py-2.5 font-normal" value={email} onChange={(event) => setEmail(event.target.value)} required />
          </label>
          <label className="block text-sm font-semibold">
            Phone
            <input type="tel" className="mt-1 block w-full rounded-md border border-line bg-cream px-3 py-2.5 font-normal" value={phone} onChange={(event) => setPhone(event.target.value)} required />
          </label>
        </div>
        <label className="block text-sm font-semibold">
          Desired move-in date
          <input type="date" className="mt-1 block w-full rounded-md border border-line bg-cream px-3 py-2.5 font-normal" value={moveInDate} onChange={(event) => setMoveInDate(event.target.value)} required />
        </label>
        <div>
          <p className="text-sm font-semibold">Roommates <span className="font-normal text-muted">(optional)</span></p>
          <p className="mt-1 text-xs text-muted">Add each roommate who should be included in this application.</p>
          <div className="mt-2 space-y-2">
            {roommates.map((roommate, index) => (
              <div key={index} className="flex gap-2">
                <input className="min-w-0 flex-1 rounded-md border border-line bg-cream px-3 py-2 font-normal" placeholder={`Roommate ${index + 1} name`} value={roommate} onChange={(event) => setRoommates((current) => current.map((item, itemIndex) => itemIndex === index ? event.target.value : item))} maxLength={200} />
                <button type="button" className="px-2 text-sm text-muted hover:text-ink" onClick={() => setRoommates((current) => current.filter((_, itemIndex) => itemIndex !== index))}>Remove</button>
              </div>
            ))}
          </div>
          <button type="button" className="mt-2 text-sm font-semibold text-brand underline" onClick={() => setRoommates((current) => [...current, ''])}>+ Add roommate</button>
        </div>
        {formError && <p className="text-sm font-semibold text-brand">{formError}</p>}
        <button type="submit" className="rounded-md bg-brand px-5 py-3 font-semibold text-white hover:bg-brand-dark">
          Continue to available apartments
        </button>
      </form>
    </section>
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
