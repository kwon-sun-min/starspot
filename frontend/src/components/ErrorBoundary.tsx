import { Component, type ReactNode } from "react";

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}
interface State {
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  state: State = { error: null };

  static getDerivedStateFromError(error: Error): State {
    return { error };
  }

  render() {
    if (this.state.error) {
      return (
        this.props.fallback ?? (
          <div className="error-panel" role="alert">
            <h2>문제가 발생했어요</h2>
            <p>{this.state.error.message}</p>
            <button onClick={() => this.setState({ error: null })}>다시 시도</button>
          </div>
        )
      );
    }
    return this.props.children;
  }
}
