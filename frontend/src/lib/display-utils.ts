/**
 * Display utility functions for AdaptiveCare UI
 */

import type { Trajectory, ActionType, LocationType } from '@/types/hospital';

// Risk score background colors
export function getRiskBgColor(riskScore: number): string {
    if (riskScore >= 70) return 'bg-red-500/10 border-red-500';
    if (riskScore >= 50) return 'bg-orange-500/10 border-orange-500';
    if (riskScore >= 30) return 'bg-yellow-500/10 border-yellow-500';
    return 'bg-green-500/10 border-green-500';
}

export function getRiskTextColor(riskScore: number): string {
    if (riskScore >= 70) return 'text-red-500';
    if (riskScore >= 50) return 'text-orange-500';
    if (riskScore >= 30) return 'text-yellow-500';
    return 'text-green-500';
}

// Trajectory information
export function getTrajectoryInfo(trajectory: Trajectory): { label: string; color: string; icon: string } {
    switch (trajectory) {
        case 'critical':
            return { label: 'Critical', color: 'text-red-500', icon: '🚨' };
        case 'deteriorating':
            return { label: 'Deteriorating', color: 'text-orange-500', icon: '📉' };
        case 'stable':
            return { label: 'Stable', color: 'text-blue-500', icon: '➡️' };
        case 'improving':
            return { label: 'Improving', color: 'text-green-500', icon: '📈' };
        default:
            return { label: 'Unknown', color: 'text-gray-500', icon: '❓' };
    }
}

// Location colors
export function getLocationColor(location: LocationType): string {
    switch (location) {
        case 'ICU':
            return 'bg-red-500/20 text-red-400';
        case 'ED':
            return 'bg-orange-500/20 text-orange-400';
        case 'Ward':
            return 'bg-blue-500/20 text-blue-400';
        case 'ED_Obs':
            return 'bg-yellow-500/20 text-yellow-400';
        case 'OR':
            return 'bg-purple-500/20 text-purple-400';
        default:
            return 'bg-gray-500/20 text-gray-400';
    }
}

// Action type info
export function getActionInfo(action: ActionType): { label: string; color: string; bgColor: string } {
    switch (action) {
        case 'escalate':
            return { label: 'Escalate', color: 'text-red-500', bgColor: 'bg-red-500/10' };
        case 'transfer':
            return { label: 'Transfer', color: 'text-orange-500', bgColor: 'bg-orange-500/10' };
        case 'admit':
            return { label: 'Admit', color: 'text-blue-500', bgColor: 'bg-blue-500/10' };
        case 'observe':
            return { label: 'Observe', color: 'text-yellow-500', bgColor: 'bg-yellow-500/10' };
        case 'delay':
            return { label: 'Delay', color: 'text-gray-500', bgColor: 'bg-gray-500/10' };
        default:
            return { label: 'Unknown', color: 'text-gray-500', bgColor: 'bg-gray-500/10' };
    }
}

// Date/time formatting
export function formatDateTime(dateString: string): string {
    try {
        const date = new Date(dateString);
        return date.toLocaleString('en-US', {
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit',
        });
    } catch {
        return dateString;
    }
}

export function formatTimestamp(dateString: string): string {
    try {
        const date = new Date(dateString);
        return date.toLocaleTimeString('en-US', {
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit',
        });
    } catch {
        return dateString;
    }
}

export function formatTimeAgo(dateString: string): string {
    try {
        const date = new Date(dateString);
        const now = new Date();
        const diffMs = now.getTime() - date.getTime();
        const diffMins = Math.floor(diffMs / 60000);

        if (diffMins < 1) return 'Just now';
        if (diffMins < 60) return `${diffMins}m ago`;

        const diffHours = Math.floor(diffMins / 60);
        if (diffHours < 24) return `${diffHours}h ago`;

        const diffDays = Math.floor(diffHours / 24);
        return `${diffDays}d ago`;
    } catch {
        return dateString;
    }
}

export function formatWaitTime(minutes: number): string {
    if (minutes < 60) return `${minutes}m`;
    const hours = Math.floor(minutes / 60);
    const mins = minutes % 60;
    if (mins === 0) return `${hours}h`;
    return `${hours}h ${mins}m`;
}

// Vitals formatting
export function formatVital(value: number, unit: string): string {
    return `${value.toFixed(1)}${unit}`;
}

export function getVitalStatus(vital: string, value: number): 'normal' | 'warning' | 'critical' {
    switch (vital) {
        case 'heart_rate':
            if (value < 40 || value > 150) return 'critical';
            if (value < 50 || value > 120) return 'warning';
            return 'normal';
        case 'oxygen_saturation':
            if (value < 88) return 'critical';
            if (value < 92) return 'warning';
            return 'normal';
        case 'blood_pressure_systolic':
            if (value < 80 || value > 200) return 'critical';
            if (value < 90 || value > 160) return 'warning';
            return 'normal';
        case 'respiratory_rate':
            if (value < 8 || value > 35) return 'critical';
            if (value < 10 || value > 25) return 'warning';
            return 'normal';
        case 'temperature':
            if (value < 35 || value > 40) return 'critical';
            if (value < 36 || value > 38) return 'warning';
            return 'normal';
        default:
            return 'normal';
    }
}

export function getVitalStatusColor(status: 'normal' | 'warning' | 'critical'): string {
    switch (status) {
        case 'critical':
            return 'text-red-500';
        case 'warning':
            return 'text-yellow-500';
        case 'normal':
            return 'text-green-500';
    }
}

// Confidence formatting
export function formatConfidence(confidence: number): string {
    return `${(confidence * 100).toFixed(0)}%`;
}

export function getConfidenceColor(confidence: number): string {
    if (confidence >= 0.8) return 'text-green-500';
    if (confidence >= 0.6) return 'text-yellow-500';
    return 'text-orange-500';
}

// Occupancy formatting
export function getOccupancyColor(rate: number): string {
    if (rate >= 0.9) return 'text-red-500';
    if (rate >= 0.75) return 'text-orange-500';
    if (rate >= 0.5) return 'text-yellow-500';
    return 'text-green-500';
}

export function formatOccupancy(rate: number): string {
    return `${(rate * 100).toFixed(0)}%`;
}
