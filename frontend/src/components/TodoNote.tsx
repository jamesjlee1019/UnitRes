import { TEAMS, type TeamName } from '../teams.ts'

/** The "not built yet" box on each team's page. Delete it once your page works. */
export default function TodoNote({ team }: { team: TeamName }) {
  const { goal, files } = TEAMS[team]
  return (
    <div className="rounded-md border-2 border-dashed border-brand bg-paper p-5">
      <p className="font-mono text-xs uppercase tracking-[0.2em] text-brand-ink">
        Not built yet · {team} team · week 1
      </p>
      <p className="mt-2 text-lg font-semibold">{goal}</p>
      <p className="mt-4 text-sm text-muted">Your code goes in:</p>
      <ul className="mt-1 space-y-1 font-mono text-sm">
        {files.map((file) => (
          <li key={file}>{file}</li>
        ))}
      </ul>
    </div>
  )
}
