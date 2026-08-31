import { render } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { AuthContextTestProvider } from "./AuthContextTestProvider";

export function renderWithProviders(
  ui,
  { route = "/", authValue = {}, routerProps = {} } = {}
) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter initialEntries={[route]} {...routerProps}>
        <AuthContextTestProvider value={authValue}>{ui}</AuthContextTestProvider>
      </MemoryRouter>
    </QueryClientProvider>
  );
}
