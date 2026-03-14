export function ErrorState({ message }: { message: string }) {
  return (
    <div className="card border-rose-200 bg-rose-50 p-4">
      <p className="text-sm text-rose-700">{message}</p>
    </div>
  );
}
