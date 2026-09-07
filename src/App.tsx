import React, { useState, useEffect, useCallback } from 'react';
import { AuthProvider, useAuth } from './context/AuthContext';
import { Navbar } from './components/Navbar';
import { Footer } from './components/Footer';
import { LandingView } from './components/LandingView';
import { AssessmentFormView } from './components/AssessmentFormView';
import { AnalysisProgressView } from './components/AnalysisProgressView';
import { ComplianceResultView } from './components/ComplianceResultView';
import { AboutStandardModal } from './components/AboutStandardModal';
import { DisclaimerBadge } from './components/DisclaimerBadge';

import { LoginView } from './components/auth/LoginView';
import { SignupView } from './components/auth/SignupView';
import { VerifyEmailView } from './components/auth/VerifyEmailView';
import { ForgotPasswordView } from './components/auth/ForgotPasswordView';
import { ResetPasswordView } from './components/auth/ResetPasswordView';
import { TrustLedgerDashboard } from './components/TrustLedgerDashboard';
import { TrustLedgerVerifyPage } from './components/TrustLedgerVerifyPage';

import { ProductFormData, AssessmentResult, ExtractedParameter } from './types/assessment';
import { EMPTY_PRODUCT_FORM } from './data/demoData';
import { assessmentService } from './services/assessmentService';
import { trustLedgerService } from './services/trustLedgerService';
import { ShieldCheck, Loader2 } from 'lucide-react';

type ViewType = 
  | 'login' 
  | 'signup' 
  | 'verify-email' 
  | 'forgot-password' 
  | 'reset-password'
  | 'dashboard'
  | 'assessment' 
  | 'analyzing' 
  | 'result'
  | 'trust-ledger'
  | 'verify';

const PUBLIC_VIEWS = ['login', 'signup', 'verify-email', 'forgot-password', 'reset-password', 'verify'];

function MainAppContent() {
  const { user, isLoading, isAuthenticated, refreshUser } = useAuth();
  const [currentView, setCurrentView] = useState<ViewType>('login');
  const [productData, setProductData] = useState<ProductFormData>(EMPTY_PRODUCT_FORM);
  const [assessmentResult, setAssessmentResult] = useState<AssessmentResult | null>(null);
  const [isRecheckAnalysis, setIsRecheckAnalysis] = useState(false);
  const [isAboutModalOpen, setIsAboutModalOpen] = useState(false);
  const [verifyPublicId, setVerifyPublicId] = useState<string | null>(null);

  // Auth helper state
  const [authEmail, setAuthEmail] = useState<string>('');
  const [authToken, setAuthToken] = useState<string>('');
  
  // Transient state for ongoing analysis
  const [pendingAnalysis, setPendingAnalysis] = useState<{
    appId: string;
    standardId: string;
    params: ExtractedParameter[];
  } | null>(null);

  // Map URL pathname & search params to ViewType
  const getViewFromUrl = useCallback((): { view: ViewType; token?: string; email?: string; publicId?: string } => {
    const pathname = window.location.pathname.replace(/^\/+|\/+$/g, '');
    const params = new URLSearchParams(window.location.search);
    const viewParam = params.get('view');
    const tokenParam = params.get('token') || undefined;
    const emailParam = params.get('email') || undefined;
    const verifyPathId = pathname.startsWith('verify/') ? pathname.replace(/^verify\//, '') : undefined;

    // Check query param first
    if (viewParam) {
      if (['login', 'signup', 'verify-email', 'forgot-password', 'reset-password'].includes(viewParam)) {
        return { view: viewParam as ViewType, token: tokenParam, email: emailParam };
      }
      if (['dashboard', 'landing'].includes(viewParam)) return { view: 'dashboard' };
      if (viewParam === 'assessment') return { view: 'assessment' };
      if (['result', 'compliance'].includes(viewParam)) return { view: 'result' };
    }

    // Check path routing
    if (pathname === 'login') return { view: 'login' };
    if (pathname === 'signup') return { view: 'signup' };
    if (pathname === 'verify-email') return { view: 'verify-email', token: tokenParam, email: emailParam };
    if (pathname === 'forgot-password') return { view: 'forgot-password' };
    if (pathname === 'reset-password') return { view: 'reset-password', token: tokenParam };
    if (pathname === 'assessment') return { view: 'assessment' };
    if (pathname === 'dashboard' || pathname === 'landing' || pathname === 'applications' || pathname === 'tracking' || pathname === 'profile' || pathname === 'settings') {
      return { view: 'dashboard' };
    }
    if (pathname === 'compliance' || pathname === 'result') return { view: 'result' };
    if (pathname === 'trust-ledger') return { view: 'trust-ledger' };
    if (pathname.startsWith('verify/')) return { view: 'verify', publicId: verifyPathId };

    // Default root path '/'
    if (tokenParam) {
      return { view: 'verify-email', token: tokenParam, email: emailParam };
    }
    return { view: 'login' };
  }, []);

  // Update browser URL on view change
  const navigateTo = useCallback((view: ViewType, replace: boolean = false, customQuery?: string, publicId?: string) => {
    setCurrentView(view);
    if (view === 'verify' && publicId) {
      setVerifyPublicId(publicId);
      const fullUrl = `/verify/${publicId}`;
      if (replace) {
        window.history.replaceState(null, '', fullUrl);
      } else {
        window.history.pushState(null, '', fullUrl);
      }
      return;
    }
    const targetPath = view === 'dashboard'
      ? '/dashboard'
      : view === 'trust-ledger'
        ? '/trust-ledger'
        : view === 'verify'
          ? '/verify'
          : `/${view}`;
    const fullUrl = customQuery ? `${targetPath}?${customQuery}` : targetPath;
    if (replace) {
      window.history.replaceState(null, '', fullUrl);
    } else {
      window.history.pushState(null, '', fullUrl);
    }
    if (view !== 'verify') {
      setVerifyPublicId(null);
    }
  }, []);

  // Sync state with URL and enforce protection
  useEffect(() => {
    if (isLoading) return; // Wait until initial session check completes

    const { view, token, email, publicId } = getViewFromUrl();
    if (token) setAuthToken(token);
    if (email) setAuthEmail(email);
    if (publicId) setVerifyPublicId(publicId);

    if (isAuthenticated) {
      // If user is authenticated and hits root '/' or '/login' or '/signup', redirect to /dashboard
      if (PUBLIC_VIEWS.includes(view)) {
        if (view === 'verify-email' || view === 'reset-password') {
          setCurrentView(view);
        } else {
          navigateTo('dashboard', true);
        }
      } else {
        setCurrentView(view);
      }
    } else {
      // Unauthenticated user attempting to access protected route -> redirect to /login
      if (!PUBLIC_VIEWS.includes(view)) {
        navigateTo('login', true);
      } else {
        setCurrentView(view);
      }
    }
  }, [isLoading, isAuthenticated, getViewFromUrl, navigateTo]);

  // Handle browser Back/Forward navigation
  useEffect(() => {
    const handlePopState = () => {
      const { view, token, email, publicId } = getViewFromUrl();
      if (token) setAuthToken(token);
      if (email) setAuthEmail(email);
      if (publicId) setVerifyPublicId(publicId);

      if (!isAuthenticated && !PUBLIC_VIEWS.includes(view)) {
        navigateTo('login', true);
      } else {
        setCurrentView(view);
      }
    };
    window.addEventListener('popstate', handlePopState);
    return () => window.removeEventListener('popstate', handlePopState);
  }, [isAuthenticated, getViewFromUrl, navigateTo]);

  // Handle form submission to start AI analysis
  const handleStartAnalysis = (
    data: ProductFormData,
    reviewedParams?: ExtractedParameter[],
    selectedStandardId?: string,
    appId?: string
  ) => {
    setProductData(data);
    setIsRecheckAnalysis(false);

    if (reviewedParams && selectedStandardId && appId) {
      setPendingAnalysis({
        appId,
        standardId: selectedStandardId,
        params: reviewedParams,
      });
    } else {
      setPendingAnalysis(null);
    }

    setCurrentView('analyzing');
  };

  // Called when analysis animation completes
  const handleAnalysisComplete = async () => {
    try {
      if (isRecheckAnalysis && assessmentResult) {
        const updated = await assessmentService.recheckProduct(assessmentResult, 84);
        setAssessmentResult(updated);
      } else if (pendingAnalysis) {
        const result = await assessmentService.runComplianceAnalysis(
          pendingAnalysis.appId,
          pendingAnalysis.standardId,
          pendingAnalysis.params,
          productData
        );
        setAssessmentResult(result);
      } else {
        const result = await assessmentService.analyzeProduct(productData);
        setAssessmentResult(result);
      }
    } catch (err) {
      console.error('Analysis completion error:', err);
    }
    navigateTo('result');
  };

  // Handle "Re-check Product" simulation
  const handleRecheck = () => {
    setIsRecheckAnalysis(true);
    setCurrentView('analyzing');
  };

  // Reset demo back to baseline
  const handleResetDemo = () => {
    setProductData(EMPTY_PRODUCT_FORM);
    setAssessmentResult(null);
    setPendingAnalysis(null);
    setIsRecheckAnalysis(false);
    navigateTo('dashboard');
  };

  const handleSignupSuccess = (email: string) => {
    setAuthEmail(email);
    navigateTo('verify-email');
  };

  const handleRegisterTrustRecord = async () => {
    const latestRecord = await trustLedgerService.createProductTrustRecord({
      product_name: assessmentResult?.productName || 'Demo BIS Product',
      manufacturer: assessmentResult?.manufacturer || 'Demo Manufacturer',
      model: assessmentResult?.modelNumber || 'MODEL-01',
      standard_id: assessmentResult?.referenceStandard || 'IS 16102 (Part 1) : 2012',
      standard_title: assessmentResult?.standardTitle || 'Self-Ballasted LED Lamps for General Lighting Services',
      standard_version: '2026',
      certificate_id: `CERT-${Date.now().toString().slice(-6)}`,
      certification_status: assessmentResult?.statusText?.toUpperCase().includes('HIGH') ? 'ACTIVE' : 'ACTIVE',
      valid_until: new Date(Date.now() + 1000 * 60 * 60 * 24 * 365).toISOString(),
      issuer: 'Authorized Issuer / Demo Authority',
    });
    navigateTo('trust-ledger');
    return latestRecord;
  };

  // Show clean loading splash screen while initializing session
  if (isLoading) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center bg-slate-50 text-slate-900">
        <div className="flex flex-col items-center gap-4 animate-in fade-in zoom-in-95 duration-200">
          <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-brand-600 to-brand-800 text-white flex items-center justify-center shadow-lg shadow-brand-500/20">
            <ShieldCheck className="w-8 h-8 text-white" />
          </div>
          <div className="text-center">
            <h1 className="text-xl font-bold tracking-tight text-slate-900">BIS One</h1>
            <p className="text-xs text-slate-500 mt-0.5">Intelligent BIS Assistant</p>
          </div>
          <div className="flex items-center gap-2 mt-2 text-xs font-medium text-slate-500">
            <Loader2 className="w-4 h-4 animate-spin text-brand-600" />
            <span>Initializing secure session...</span>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex flex-col bg-slate-50 text-slate-900">
      {/* Top Banner Disclaimer */}
      <DisclaimerBadge variant="banner" />

      {/* Main Navigation */}
      <Navbar
        currentView={currentView}
        onNavigate={(view) => navigateTo(view as ViewType)}
        onOpenAbout={() => setIsAboutModalOpen(true)}
        onResetDemo={handleResetDemo}
        hasResult={!!assessmentResult}
        activeStandardId={assessmentResult?.referenceStandard || pendingAnalysis?.standardId}
      />

      {/* Main Content View */}
      <main className="flex-1">
        {/* PUBLIC AUTHENTICATION VIEWS */}
        {currentView === 'login' && (
          <LoginView
            onNavigate={(view) => navigateTo(view as ViewType)}
            onSuccessRedirect={() => navigateTo('dashboard')}
          />
        )}

        {currentView === 'signup' && (
          <SignupView
            onNavigate={(view) => navigateTo(view as ViewType)}
            onRegistered={handleSignupSuccess}
          />
        )}

        {currentView === 'verify-email' && (
          <VerifyEmailView
            email={authEmail}
            token={authToken}
            onNavigate={(view) => navigateTo(view as ViewType)}
          />
        )}

        {currentView === 'forgot-password' && (
          <ForgotPasswordView
            onNavigate={(view) => navigateTo(view as ViewType)}
          />
        )}

        {currentView === 'reset-password' && (
          <ResetPasswordView
            token={authToken}
            onNavigate={(view) => navigateTo(view as ViewType)}
          />
        )}

        {/* PROTECTED SYSTEM VIEWS (Only accessible when authenticated) */}
        {isAuthenticated && (
          <>
            {(currentView === 'dashboard' || (currentView as string) === 'landing') && (
              <LandingView
                onStartAssessment={() => navigateTo('assessment')}
                onOpenAbout={() => setIsAboutModalOpen(true)}
              />
            )}

            {currentView === 'assessment' && (
              <AssessmentFormView
                initialData={productData}
                onSubmit={handleStartAnalysis}
              />
            )}

            {currentView === 'analyzing' && (
              <AnalysisProgressView
                onComplete={handleAnalysisComplete}
                isRecheck={isRecheckAnalysis}
              />
            )}

            {currentView === 'result' && assessmentResult && (
              <ComplianceResultView
                assessment={assessmentResult}
                onRecheck={handleRecheck}
                onEditSpecs={() => navigateTo('assessment')}
                onRegisterTrustLedger={handleRegisterTrustRecord}
              />
            )}

            {currentView === 'trust-ledger' && (
              <TrustLedgerDashboard onViewProduct={(publicId) => navigateTo('verify', false, undefined, publicId)} />
            )}

            {currentView === 'verify' && (
              <TrustLedgerVerifyPage publicProductId={verifyPublicId || undefined} />
            )}
          </>
        )}
      </main>

      {/* Footer */}
      <Footer onOpenAbout={() => setIsAboutModalOpen(true)} />

      {/* About Standard Modal */}
      {isAboutModalOpen && (
        <AboutStandardModal
          onClose={() => setIsAboutModalOpen(false)}
          activeStandardId={assessmentResult?.referenceStandard || pendingAnalysis?.standardId}
        />
      )}
    </div>
  );
}

export function App() {
  return (
    <AuthProvider>
      <MainAppContent />
    </AuthProvider>
  );
}

export default App;
