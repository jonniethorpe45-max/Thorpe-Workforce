export function ErrorState({ message }: { message: string }) {
  return (
    <div className="card border-rose-300/40 bg-rose-950/20 p-4">
      <p className="text-sm text-rose-200">{message}</p>
    </div>
  );
}
