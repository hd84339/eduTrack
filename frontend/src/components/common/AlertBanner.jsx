import React from 'react';
import { AlertCircle, CheckCircle, Info, XCircle, X } from 'lucide-react';

const ALERT_CONFIG = {
  error: {
    bg: 'bg-rose-50 border-rose-200 text-rose-800',
    icon: XCircle,
    iconColor: 'text-rose-500',
  },
  warning: {
    bg: 'bg-amber-50 border-amber-200 text-amber-800',
    icon: AlertCircle,
    iconColor: 'text-amber-500',
  },
  success: {
    bg: 'bg-emerald-50 border-emerald-200 text-emerald-800',
    icon: CheckCircle,
    iconColor: 'text-emerald-500',
  },
  info: {
    bg: 'bg-sky-50 border-sky-200 text-sky-800',
    icon: Info,
    iconColor: 'text-sky-500',
  },
};

export const AlertBanner = ({ type = 'error', message, title, onClose, className = '' }) => {
  if (!message) return null;

  const config = ALERT_CONFIG[type] || ALERT_CONFIG.error;
  const IconComponent = config.icon;

  return (
    <div className={`p-4 rounded-lg border ${config.bg} flex items-start space-x-3 ${className}`}>
      <IconComponent className={`w-5 h-5 mt-0.5 flex-shrink-0 ${config.iconColor}`} />
      <div className="flex-1 text-sm">
        {title && <h4 className="font-semibold mb-1">{title}</h4>}
        <div className="font-medium whitespace-pre-line">{message}</div>
      </div>
      {onClose && (
        <button
          onClick={onClose}
          type="button"
          className="text-slate-400 hover:text-slate-600 transition-colors p-1"
        >
          <X className="w-4 h-4" />
        </button>
      )}
    </div>
  );
};

export default AlertBanner;

