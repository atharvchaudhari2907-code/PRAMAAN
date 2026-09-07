import React, { useState, useEffect } from 'react';
import { authService } from '../../services/authService';
import { KeyRound, Eye, EyeOff, CheckCircle, AlertCircle, ArrowLeft, ShieldCheck, Check, X } from 'lucide-react';

interface ResetPasswordViewProps {
  token?: string;
  onNavigate: (view: string) => void;
}

export const ResetPasswordView: React.FC<ResetPasswordViewProps> = ({
  token: initialToken,
  onNavigate
}) => {
  const [token, setToken] = useState(initialToken || '');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [success, setSuccess] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  useEffect(() => {
    // Parse token from URL if not supplied as prop
    if (!initialToken) {
      const urlParams = new URLSearchParams(window.location.search);
      const urlToken = urlParams.get('token');
      if (urlToken) {
        setToken(urlToken);
      }
    }
  }, [initialToken]);

  // Password requirement rules
  const hasMinLength = newPassword.length >= 8;
  const hasUpperCase = /[A-Z]/.test(newPassword);
  const hasLowerCase = /[a-z]/.test(newPassword);
  const hasNumber = /\d/.test(newPassword);
  const hasSpecial = /[@$!%*?&#^()_\-+={}\[\]|:;"'<>,.?/~`]/.test(newPassword);
  const isPasswordValid = hasMinLength && hasUpperCase && hasLowerCase && hasNumber && hasSpecial;
  const passwordsMatch = newPassword === confirmPassword && confirmPassword.length > 0;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage(null);

    if (!token.trim()) {
      setErrorMessage('Password reset token is missing or invalid. Please request a new reset link.');
      return;
    }

    if (!isPasswordValid) {
      setErrorMessage('Please ensure your new password meets all security requirements.');
      return;
    }

    if (newPassword !== confirmPassword) {
      setErrorMessage('Passwords do not match.');
      return;
    }

    try {
      setSubmitting(true);
      await authService.resetPassword({
        token: token.trim(),
        new_password: newPassword,
        confirm_password: confirmPassword,
      });
      setSuccess(true);
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to reset password. The link may be expired.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="min-h-[85vh] flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8 bg-gradient-to-br from-slate-50 via-blue-50/20 to-slate-100">
      <div className="max-w-md w-full bg-white rounded-2xl shadow-xl border border-slate-100 p-8">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="w-16 h-16 bg-blue-100 text-blue-700 rounded-2xl flex items-center justify-center mx-auto mb-4 shadow-inner">
            <KeyRound className="w-8 h-8" />
          </div>
          <h2 className="text-2xl font-bold text-slate-900 tracking-tight">Set New Password</h2>
          <p className="text-sm text-slate-500 mt-2">
            Please choose a strong password for your BIS One account.
          </p>
        </div>

        {/* Error banner */}
        {errorMessage && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-xl flex items-start gap-3 text-red-700 text-sm animate-in fade-in duration-200">
            <AlertCircle className="w-5 h-5 flex-shrink-0 mt-0.5" />
            <div className="flex-1">
              <span className="font-medium">Error:</span> {errorMessage}
            </div>
          </div>
        )}

        {/* Success State */}
        {success ? (
          <div className="text-center space-y-6 animate-in zoom-in-95 duration-300">
            <div className="p-4 bg-emerald-50 border border-emerald-200 rounded-xl flex flex-col items-center gap-2 text-emerald-800 text-sm">
              <CheckCircle className="w-10 h-10 text-emerald-600 mb-1" />
              <p className="font-semibold text-base">Password Reset Successfully!</p>
              <p className="text-emerald-700 text-center">
                Your password has been securely updated. All other active sessions have been invalidated for security.
              </p>
            </div>

            <button
              onClick={() => onNavigate('login')}
              className="w-full py-3.5 px-4 bg-blue-700 hover:bg-blue-800 text-white font-medium rounded-xl transition-all shadow-md hover:shadow-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 flex items-center justify-center gap-2"
            >
              Sign In to Your Account
            </button>
          </div>
        ) : (
          /* Form */
          <form onSubmit={handleSubmit} className="space-y-5">
            {/* Manual Token Input if not in URL */}
            {!initialToken && (
              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5">
                  Reset Token
                </label>
                <input
                  type="text"
                  required
                  value={token}
                  onChange={(e) => setToken(e.target.value)}
                  placeholder="Paste reset token from email"
                  className="w-full px-4 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-slate-900 text-sm font-mono focus:bg-white focus:outline-none focus:ring-2 focus:ring-blue-600 focus:border-transparent transition-all"
                />
              </div>
            )}

            {/* New Password */}
            <div>
              <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5">
                New Password
              </label>
              <div className="relative">
                <input
                  type={showPassword ? 'text' : 'password'}
                  required
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  placeholder="••••••••"
                  className="w-full px-4 py-2.5 pr-10 bg-slate-50 border border-slate-200 rounded-xl text-slate-900 text-sm focus:bg-white focus:outline-none focus:ring-2 focus:ring-blue-600 focus:border-transparent transition-all"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600"
                >
                  {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>

            {/* Confirm Password */}
            <div>
              <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5">
                Confirm New Password
              </label>
              <div className="relative">
                <input
                  type={showConfirmPassword ? 'text' : 'password'}
                  required
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  placeholder="••••••••"
                  className={`w-full px-4 py-2.5 pr-10 bg-slate-50 border rounded-xl text-slate-900 text-sm focus:bg-white focus:outline-none focus:ring-2 transition-all ${
                    confirmPassword && !passwordsMatch
                      ? 'border-red-300 focus:ring-red-500'
                      : 'border-slate-200 focus:ring-blue-600 focus:border-transparent'
                  }`}
                />
                <button
                  type="button"
                  onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600"
                >
                  {showConfirmPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
              {confirmPassword && !passwordsMatch && (
                <p className="text-xs text-red-600 mt-1">Passwords do not match</p>
              )}
            </div>

            {/* Password Requirements Card */}
            <div className="p-3.5 bg-slate-50 rounded-xl border border-slate-200 text-xs space-y-1.5">
              <span className="font-semibold text-slate-700 block mb-1 flex items-center gap-1.5">
                <ShieldCheck className="w-3.5 h-3.5 text-blue-600" />
                Password Requirements:
              </span>
              <div className="grid grid-cols-2 gap-1 text-slate-600">
                <div className={`flex items-center gap-1.5 ${hasMinLength ? 'text-emerald-600 font-medium' : ''}`}>
                  {hasMinLength ? <Check className="w-3 h-3" /> : <X className="w-3 h-3 text-slate-400" />}
                  8+ characters
                </div>
                <div className={`flex items-center gap-1.5 ${hasUpperCase ? 'text-emerald-600 font-medium' : ''}`}>
                  {hasUpperCase ? <Check className="w-3 h-3" /> : <X className="w-3 h-3 text-slate-400" />}
                  Uppercase letter
                </div>
                <div className={`flex items-center gap-1.5 ${hasLowerCase ? 'text-emerald-600 font-medium' : ''}`}>
                  {hasLowerCase ? <Check className="w-3 h-3" /> : <X className="w-3 h-3 text-slate-400" />}
                  Lowercase letter
                </div>
                <div className={`flex items-center gap-1.5 ${hasNumber ? 'text-emerald-600 font-medium' : ''}`}>
                  {hasNumber ? <Check className="w-3 h-3" /> : <X className="w-3 h-3 text-slate-400" />}
                  Number
                </div>
                <div className={`col-span-2 flex items-center gap-1.5 ${hasSpecial ? 'text-emerald-600 font-medium' : ''}`}>
                  {hasSpecial ? <Check className="w-3 h-3" /> : <X className="w-3 h-3 text-slate-400" />}
                  Special character (!@#$%^&*)
                </div>
              </div>
            </div>

            <button
              type="submit"
              disabled={submitting || !isPasswordValid || !passwordsMatch || !token.trim()}
              className="w-full py-3 px-4 bg-blue-700 hover:bg-blue-800 disabled:opacity-50 disabled:cursor-not-allowed text-white font-medium rounded-xl transition-all shadow-md hover:shadow-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 flex items-center justify-center gap-2"
            >
              {submitting ? (
                <>
                  <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  Updating Password...
                </>
              ) : (
                'Set New Password'
              )}
            </button>
          </form>
        )}

        {/* Back to Login */}
        <div className="mt-6 pt-6 border-t border-slate-100 text-center">
          <button
            onClick={() => onNavigate('login')}
            className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-600 hover:text-slate-900 transition-colors"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            Back to Sign In
          </button>
        </div>
      </div>
    </div>
  );
};
