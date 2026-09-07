import React, { useState, useEffect } from 'react';
import { authService } from '../../services/authService';
import { Mail, CheckCircle2, AlertCircle, Loader2, ArrowRight, RotateCcw } from 'lucide-react';

interface VerifyEmailViewProps {
  email?: string;
  token?: string;
  onNavigate: (view: any) => void;
}

export const VerifyEmailView: React.FC<VerifyEmailViewProps> = ({
  email: initialEmail = '',
  token: initialToken = '',
  onNavigate,
}) => {
  const [email, setEmail] = useState(initialEmail);
  const [token, setToken] = useState(initialToken);
  const [isVerifying, setIsVerifying] = useState(false);
  const [isResending, setIsResending] = useState(false);
  const [verificationSuccess, setVerificationSuccess] = useState(false);
  const [resendSuccessMessage, setResendSuccessMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [resendCooldown, setResendCooldown] = useState(0);

  // Auto-detect token from URL query string if present
  useEffect(() => {
    const urlParams = new URLSearchParams(window.location.search);
    const urlToken = urlParams.get('token');
    if (urlToken && !token) {
      setToken(urlToken);
      handleVerify(urlToken);
    }
  }, []);

  // Cooldown countdown timer
  useEffect(() => {
    if (resendCooldown > 0) {
      const timer = setTimeout(() => setResendCooldown(resendCooldown - 1), 1000);
      return () => clearTimeout(timer);
    }
  }, [resendCooldown]);

  const handleVerify = async (tokenToVerify: string) => {
    setIsVerifying(true);
    setError(null);
    try {
      await authService.verifyEmail(tokenToVerify);
      setVerificationSuccess(true);
    } catch (err: any) {
      setError(err.message || 'Verification link is invalid or has expired.');
    } finally {
      setIsVerifying(false);
    }
  };

  const handleResend = async () => {
    if (!email) {
      setError('Please provide an email address to resend verification.');
      return;
    }
    if (resendCooldown > 0) return;

    setIsResending(true);
    setError(null);
    setResendSuccessMessage(null);

    try {
      const res = await authService.resendVerification(email);
      setResendSuccessMessage(res.message || 'A new verification link has been sent to your email.');
      setResendCooldown(60); // 60s rate limit
    } catch (err: any) {
      setError(err.message || 'Failed to resend verification email.');
    } finally {
      setIsResending(false);
    }
  };

  return (
    <div className="min-h-[calc(100vh-140px)] flex items-center justify-center px-4 py-12">
      <div className="max-w-md w-full bg-white rounded-2xl border border-slate-200 shadow-xl overflow-hidden animate-in fade-in zoom-in-95 duration-200">
        {/* Verification Success State */}
        {verificationSuccess ? (
          <div className="p-8 text-center space-y-4">
            <div className="w-14 h-14 mx-auto rounded-2xl bg-emerald-50 border border-emerald-200 text-emerald-600 flex items-center justify-center">
              <CheckCircle2 className="w-8 h-8" />
            </div>
            <h2 className="text-xl font-bold text-slate-900 tracking-tight">Email Verified Successfully!</h2>
            <p className="text-xs text-slate-600 leading-relaxed">
              Your account has been verified. You can now access your pre-certification dashboard, AI document analyzer, and regulatory dossiers.
            </p>
            <button
              type="button"
              onClick={() => onNavigate('login')}
              className="w-full py-2.5 px-4 bg-brand-600 hover:bg-brand-700 text-white text-xs font-bold rounded-lg shadow-sm shadow-brand-600/30 flex items-center justify-center gap-2 transition-all cursor-pointer mt-4"
            >
              <span>Proceed to Sign In</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>
        ) : isVerifying ? (
          <div className="p-12 text-center space-y-4">
            <Loader2 className="w-10 h-10 mx-auto animate-spin text-brand-600" />
            <h3 className="text-base font-bold text-slate-900">Verifying your email...</h3>
            <p className="text-xs text-slate-500">Please wait while we validate your security token.</p>
          </div>
        ) : (
          /* Check Email State */
          <div>
            <div className="px-8 pt-8 pb-6 bg-gradient-to-r from-slate-50 to-white border-b border-slate-100 text-center">
              <div className="w-14 h-14 mx-auto rounded-2xl bg-amber-50 border border-amber-200 text-amber-600 flex items-center justify-center mb-4">
                <Mail className="w-7 h-7" />
              </div>
              <h2 className="text-xl font-bold text-slate-900 tracking-tight">Demo verification mode</h2>
              <p className="text-xs text-slate-500 mt-1">This local app does not send real email messages.</p>
            </div>

            <div className="p-8 space-y-5">
              {email && (
                <div className="p-3 bg-slate-50 rounded-xl border border-slate-200/80 text-center">
                  <span className="text-xs font-bold text-slate-800 break-all">{email}</span>
                </div>
              )}

              {error && (
                <div className="p-3.5 rounded-xl bg-rose-50 border border-rose-200 text-rose-700 text-xs flex items-start gap-2.5 animate-in fade-in">
                  <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5" />
                  <span>{error}</span>
                </div>
              )}

              {resendSuccessMessage && (
                <div className="p-3.5 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs flex items-start gap-2.5 animate-in fade-in">
                  <CheckCircle2 className="w-4 h-4 flex-shrink-0 mt-0.5 text-emerald-600" />
                  <span>{resendSuccessMessage}</span>
                </div>
              )}

              <p className="text-xs text-slate-600 leading-relaxed text-center">
                In this demo environment, the account is immediately activated locally. There is no actual email delivery or verification link to click.
              </p>

              {!email && (
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1.5">
                    Enter email to resend link
                  </label>
                  <input
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="name@company.com"
                    className="w-full px-3 py-2 text-xs rounded-lg border border-slate-200 focus:outline-none focus:ring-2 focus:ring-brand-500/20 focus:border-brand-600"
                  />
                </div>
              )}

              <button
                type="button"
                onClick={() => onNavigate('login')}
                className="w-full py-2.5 px-4 bg-brand-600 hover:bg-brand-700 text-white text-xs font-bold rounded-lg shadow-sm shadow-brand-600/30 flex items-center justify-center gap-2 transition-all cursor-pointer"
              >
                <span>Continue to login</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </button>

              <button
                type="button"
                onClick={handleResend}
                disabled={isResending || resendCooldown > 0}
                className="w-full py-2.5 px-4 bg-slate-100 hover:bg-slate-200/80 disabled:opacity-60 text-slate-800 text-xs font-bold rounded-lg border border-slate-200 flex items-center justify-center gap-2 transition-colors cursor-pointer"
              >
                {isResending ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin text-slate-600" />
                    <span>Checking demo status...</span>
                  </>
                ) : resendCooldown > 0 ? (
                  <span>Retry in {resendCooldown}s</span>
                ) : (
                  <>
                    <RotateCcw className="w-3.5 h-3.5 text-slate-600" />
                    <span>Refresh local demo status</span>
                  </>
                )}
              </button>

              <div className="pt-2 text-center">
                <button
                  type="button"
                  onClick={() => onNavigate('login')}
                  className="text-xs font-semibold text-slate-500 hover:text-slate-800 transition-colors cursor-pointer"
                >
                  &larr; Back to login
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
