import { Toaster } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import NotFound from "@/pages/NotFound";
import { Route, Switch } from "wouter";
import ErrorBoundary from "./components/ErrorBoundary";
import { ThemeProvider } from "./contexts/ThemeContext";
import { CandidateProvider } from "./contexts/CandidateContext";
import Home from "./pages/Home";
import Register from "./pages/Register";
import Dashboard from "./pages/Dashboard";
import AptitudeTest from "./pages/AptitudeTest";
import SafetyTraining from "./pages/SafetyTraining";
import SafetyLesson from "./pages/SafetyLesson";
import AdminResults from "./pages/AdminResults";
import RecruitMe from "./pages/RecruitMe";

function Router() {
  // make sure to consider if you need authentication for certain routes
  return (
    <Switch>
      <Route path={"/recruitme"} component={RecruitMe} />
      <Route path={"/"} component={Home} />
      <Route path={"/register"} component={Register} />
      <Route path={"/dashboard"} component={Dashboard} />
      <Route path={"/aptitude"} component={AptitudeTest} />
      <Route path={"/safety"} component={SafetyTraining} />
      <Route path={"/safety/:lessonId"} component={SafetyLesson} />
      <Route path={"/admin/results"} component={AdminResults} />
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
        defaultTheme="light"
        // switchable
      >
        <CandidateProvider>
          <TooltipProvider>
            <Toaster />
            <Router />
          </TooltipProvider>
        </CandidateProvider>
      </ThemeProvider>
    </ErrorBoundary>
  );
}

export default App;
