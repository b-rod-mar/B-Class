import { clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs) {
  return twMerge(clsx(inputs));
}

export function formatDate(date) {
  if (!date) return '-';
  return new Date(date).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  });
}

export function getConfidenceColor(score) {
  if (score >= 85) return 'confidence-high';
  if (score >= 60) return 'confidence-medium';
  return 'confidence-low';
}

export function getConfidenceLabel(score) {
  if (score >= 85) return 'High';
  if (score >= 60) return 'Medium';
  return 'Low';
}

export function getStatusColor(status) {
  switch (status) {
    case 'auto_approved':
      return 'status-approved';
    case 'needs_review':
      return 'status-review';
    case 'rejected':
      return 'status-rejected';
    default:
      return 'status-review';
  }
}

export function getStatusLabel(status) {
  switch (status) {
    case 'auto_approved':
      return 'Auto Approved';
    case 'needs_review':
      return 'Needs Review';
    case 'reviewed':
      return 'Reviewed';
    case 'rejected':
      return 'Rejected';
    default:
      return status;
  }
}

export function formatCurrency(value) {
  if (value === null || value === undefined) return '-';
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD'
  }).format(value);
}

export function formatNumber(value) {
  if (value === null || value === undefined) return '-';
  return new Intl.NumberFormat('en-US').format(value);
}
