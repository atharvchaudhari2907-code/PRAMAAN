import React, { useState, useRef, useEffect } from 'react';
import { ShieldCheck, FileText, RotateCcw, Hash, User as UserIcon, LogOut, ChevronDown, CheckCircle2 } from 'lucide-react';
import { DisclaimerBadge } from './DisclaimerBadge';
import { BlockchainVerifyModal } from './BlockchainVerifyModal';
import { useAuth } from '../context/AuthContext';

interface NavbarProps {
  currentView: string;
  onNavigate: (view: string) => void;
  onOpenAbout: () => void;
  onResetDemo: () => void;
  hasResult: boolean;
  activeStandardId?: string;
}

export const Navbar: React.FC<NavbarProps> = ({
  currentView,
  onNavigate,
  onOpenAbout,
  onResetDemo,
  hasResult,
  activeStandardId,
}) => {
  const [showVerifyModal, setShowVerifyModal] = useState(false);
  const [showUserDropdown, setShowUserDropdown] = useState(false);
  const { user, isAuthenticated, logout } = useAuth();
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Close dropdown on outside click
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setShowUserDropdown(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleLogout = async () => {
    setShowUserDropdown(false);
    await logout();
    onNavigate('landing');
  };

  const getUserInitials = () => {
    if (!user) return 'U';
    if (user.full_name) {
      const parts = user.full_name.trim().split(' ');
      if (parts.length >= 2) return `${parts[0][0]}${parts[1][0]}`.toUpperCase();
      return parts[0].substring(0, 2).toUpperCase();
    }
    return user.email.substring(0, 2).toUpperCase();
  };

  return (
    <>
      <header className="sticky top-0 z-40 bg-white/95 backdrop-blur-md border-b border-slate-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            {/* Brand Logo */}
            <div
              className="flex items-center gap-3 cursor-pointer group"
              onClick={() => onNavigate('landing')}
            >
              <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-brand-600 to-brand-800 text-white flex items-center justify-center shadow-sm shadow-brand-500/20 group-hover:scale-105 transition-transform">
                <ShieldCheck className="w-5 h-5 text-white" />
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <span className="font-bold text-lg text-slate-900 tracking-tight">
                    BIS AI Assistant
                  </span>
                  <DisclaimerBadge />
                </div>
                <p className="text-[11px] text-slate-500 -mt-0.5 hidden sm:block">
                  Universal Pre-Certification Readiness Engine
                </p>
              </div>
            </div>

            {/* Navigation Links */}
            <nav className="flex items-center gap-1 sm:gap-2.5">
              {isAuthenticated && (
                <>
                  <button
                    onClick={() => onNavigate('dashboard')}
                    className={`px-3 py-1.5 text-xs font-semibold rounded-lg transition-colors ${
                      currentView === 'landing' || currentView === 'dashboard'
                        ? 'text-brand-700 bg-brand-50'
                        : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
                    }`}
                  >
                    Overview
                  </button>

                  <button
                    onClick={() => onNavigate('assessment')}
                    className={`px-3 py-1.5 text-xs font-semibold rounded-lg transition-colors ${
                      currentView === 'assessment' || currentView === 'analyzing'
                        ? 'text-brand-700 bg-brand-50'
                        : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
                    }`}
                  >
                    Assessment
                  </button>

                  {hasResult && (
                    <button
                      onClick={() => onNavigate('result')}
                      className={`px-3 py-1.5 text-xs font-semibold rounded-lg transition-colors ${
                        currentView === 'result' || currentView === 'compliance'
                          ? 'text-brand-700 bg-brand-50'
                          : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
                      }`}
                    >
                      Dashboard
                    </button>
                  )}

                  <button
                    onClick={onOpenAbout}
                    className="hidden md:flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold text-slate-600 hover:text-slate-900 hover:bg-slate-100 rounded-lg transition-colors"
                    title="Browse Indian Standards catalog and clauses"
                  >
                    <FileText className="w-3.5 h-3.5 text-slate-500" />
                    <span>{activeStandardId ? `Standard: ${activeStandardId}` : 'Standards'}</span>
                  </button>

                  <button
                    onClick={() => setShowVerifyModal(true)}
                    className="hidden lg:flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold text-indigo-700 hover:text-indigo-900 bg-indigo-50/70 hover:bg-indigo-100 rounded-lg border border-indigo-200 transition-colors"
                    title="Verify Certificate Hash Integrity"
                  >
                    <Hash className="w-3.5 h-3.5 text-indigo-600" />
                    <span>Verify</span>
                  </button>

                  {/* Quick Demo Reset */}
                  <button
                    onClick={onResetDemo}
                    className="hidden sm:flex items-center gap-1.5 px-2.5 py-1.5 text-xs font-medium text-slate-500 hover:text-brand-700 hover:bg-brand-50 rounded-lg border border-transparent hover:border-brand-200 transition-all"
                    title="Reset assessment back to default state"
                  >
                    <RotateCcw className="w-3.5 h-3.5" />
                    <span>Reset</span>
                  </button>

                  <div className="h-4 w-px bg-slate-200 mx-1" />
                </>
              )}

              {/* Authentication Status / Profile */}
              {isAuthenticated && user ? (
                <div className="relative" ref={dropdownRef}>
                  <button
                    onClick={() => setShowUserDropdown(!showUserDropdown)}
                    className="flex items-center gap-2 py-1 px-2 rounded-xl hover:bg-slate-100 transition-colors border border-slate-200 bg-slate-50/50"
                  >
                    {user.avatar_url ? (
                      <img
                        src={user.avatar_url}
                        alt={user.full_name || user.email}
                        className="w-7 h-7 rounded-lg object-cover border border-slate-200"
                      />
                    ) : (
                      <div className="w-7 h-7 rounded-lg bg-blue-600 text-white flex items-center justify-center font-bold text-xs shadow-sm">
                        {getUserInitials()}
                      </div>
                    )}
                    <div className="hidden sm:flex flex-col text-left">
                      <span className="text-xs font-semibold text-slate-900 max-w-[110px] truncate leading-tight">
                        {user.full_name || user.email.split('@')[0]}
                      </span>
                      <span className="text-[10px] text-slate-500 leading-tight">
                        {user.role === 'admin' ? 'Administrator' : user.company_name || 'Manufacturer'}
                      </span>
                    </div>
                    <ChevronDown className="w-3.5 h-3.5 text-slate-400" />
                  </button>

                  {/* Dropdown Menu */}
                  {showUserDropdown && (
                    <div className="absolute right-0 mt-2 w-64 bg-white rounded-2xl shadow-xl border border-slate-100 py-2 z-50 animate-in fade-in slide-in-from-top-2 duration-150">
                      <div className="px-4 py-3 border-b border-slate-100">
                        <p className="text-xs font-semibold text-slate-900">{user.full_name || 'User'}</p>
                        <p className="text-xs text-slate-500 truncate">{user.email}</p>
                        {user.company_name && (
                          <div className="mt-1.5 flex items-center gap-1 text-[11px] text-blue-700 bg-blue-50 px-2 py-0.5 rounded-md font-medium">
                            <CheckCircle2 className="w-3 h-3 text-blue-600" />
                            {user.company_name}
                          </div>
                        )}
                      </div>

                      <div className="px-2 py-1.5">
                        <button
                          onClick={() => {
                            setShowUserDropdown(false);
                            onNavigate('assessment');
                          }}
                          className="w-full text-left px-3 py-2 text-xs font-medium text-slate-700 hover:bg-slate-50 rounded-lg transition-colors flex items-center gap-2"
                        >
                          <ShieldCheck className="w-4 h-4 text-slate-400" />
                          New Assessment
                        </button>
                        {hasResult && (
                          <button
                            onClick={() => {
                              setShowUserDropdown(false);
                              onNavigate('result');
                            }}
                            className="w-full text-left px-3 py-2 text-xs font-medium text-slate-700 hover:bg-slate-50 rounded-lg transition-colors flex items-center gap-2"
                          >
                            <FileText className="w-4 h-4 text-slate-400" />
                            My Compliance Report
                          </button>
                        )}
                      </div>

                      <div className="border-t border-slate-100 pt-1.5 px-2">
                        <button
                          onClick={handleLogout}
                          className="w-full text-left px-3 py-2 text-xs font-medium text-red-600 hover:bg-red-50 rounded-lg transition-colors flex items-center gap-2"
                        >
                          <LogOut className="w-4 h-4 text-red-500" />
                          Sign Out
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              ) : (
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => onNavigate('login')}
                    className="px-3 py-1.5 text-xs font-semibold text-slate-700 hover:text-slate-900 hover:bg-slate-100 rounded-lg transition-colors"
                  >
                    Sign In
                  </button>
                  <button
                    onClick={() => onNavigate('signup')}
                    className="px-3.5 py-1.5 text-xs font-semibold text-white bg-blue-700 hover:bg-blue-800 rounded-lg shadow-sm hover:shadow transition-all"
                  >
                    Get Started
                  </button>
                </div>
              )}
            </nav>
          </div>
        </div>
      </header>

      {showVerifyModal && (
        <BlockchainVerifyModal onClose={() => setShowVerifyModal(false)} />
      )}
    </>
  );
};

