import { Toaster } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import NotFound from "@/pages/NotFound";
import { Route, Switch } from "wouter";
import ErrorBoundary from "./components/ErrorBoundary";
import { ThemeProvider } from "./contexts/ThemeContext";
import { AudioProvider } from "./contexts/AudioContext";
import Landing from "./pages/Landing";
import AudioPreview from "./pages/AudioPreview";
import Analysis from "./pages/Analysis";

function Router() {
  return (
    <Switch>
      <Route path={"/"} component={Landing} />
      <Route path={"/preview"} component={AudioPreview} />
      <Route path={"/analysis"} component={Analysis} />
      <Route path={"/404"} component={NotFound} />
      {/* Final fallback route */}
      <Route component={NotFound} />
    </Switch>
  );
}

// NOTE: About Theme
// - First choose a default theme according to your design style (dark or light bg), than change color palette in index.css
//   to keep consistent foreground/background color across components
// - If you want to make theme switchable, pass `switchable` ThemeProvider and use `useTheme` hook

function App() {
  return (
    <ErrorBoundary>
      <ThemeProvider
        defaultTheme="dark"
      >
        <AudioProvider>
          <TooltipProvider>
            <Toaster />
            <Router />
          </TooltipProvider>
        </AudioProvider>
      </ThemeProvider>
    </ErrorBoundary>
  );
}

export default App;
