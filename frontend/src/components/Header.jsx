export default function Header() {
  return (
    <header className="flex flex-col items-center justify-center pt-8 pb-6 px-4">
      <h1 className="text-xl font-bold tracking-[0.1em] select-none">
        <span style={{ color: 'var(--sub)' }}>그레이</span>
        <span style={{ color: 'var(--text)' }}>셰프</span>
      </h1>
      <p
        className="text-[10px] tracking-[0.35em] uppercase mt-1 select-none"
        style={{ color: 'var(--gold)' }}
      >
        grey chef
      </p>
      <div
        className="mt-4 w-8 h-px"
        style={{ backgroundColor: 'var(--gold)' }}
      />
    </header>
  )
}
