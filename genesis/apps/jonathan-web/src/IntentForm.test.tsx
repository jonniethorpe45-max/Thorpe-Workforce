import { describe, expect, it, vi } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { IntentForm } from "@genesis/ui";

describe("IntentForm", () => {
  it("submits the message", async () => {
    const onSubmit = vi.fn().mockResolvedValue(undefined);
    render(<IntentForm onSubmit={onSubmit} />);
    fireEvent.change(screen.getByLabelText(/ask jonathan/i), {
      target: { value: "Schedule a meeting with Bob" },
    });
    fireEvent.click(screen.getByRole("button", { name: /submit intent/i }));
    await waitFor(() => expect(onSubmit).toHaveBeenCalledWith("Schedule a meeting with Bob"));
  });
});
