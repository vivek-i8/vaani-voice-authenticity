import React from 'react';
import { motion } from 'framer-motion';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';

/**
 * Pitch Stability Chart Component
 * Design: Line chart showing pitch fluctuation over time
 * X-axis: Time, Y-axis: Pitch frequency
 * Line color: Teal
 * Hover: Display tooltip with pitch value and timestamp
 */
interface PitchStabilityChartProps {
  signals?: {
    pitch_variance: number;
    spectral_drift: number;
    zcr_variance: number;
  };
}

export default function PitchStabilityChart({ signals }: PitchStabilityChartProps) {
  // Generate mock pitch data
  const generatePitchData = () => {
    const data = [];
    for (let i = 0; i < 50; i++) {
      data.push({
        time: `${i * 0.1}s`,
        pitch: 200 + Math.sin(i * 0.2) * 50 + Math.random() * 20,
      });
    }
    return data;
  };

  const data = generatePitchData();

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.6, delay: 0.1 }}
      className="glass-card p-8 md:p-9 h-full"
    >
      <h3 className="text-gray-400 text-sm font-medium mb-6 font-light">Pitch Stability</h3>

      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(255, 255, 255, 0.1)" />
          <XAxis
            dataKey="time"
            stroke="rgba(255, 255, 255, 0.3)"
            tick={{ fontSize: 12 }}
          />
          <YAxis
            stroke="rgba(255, 255, 255, 0.3)"
            tick={{ fontSize: 12 }}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: 'rgba(15, 23, 42, 0.9)',
              border: '1px solid rgba(45, 212, 191, 0.3)',
              borderRadius: '8px',
            }}
            labelStyle={{ color: '#E5E7EB' }}
            formatter={(value: number) => [`${Math.round(value)} Hz`, 'Pitch']}
          />
          <Line
            type="monotone"
            dataKey="pitch"
            stroke="#2DD4BF"
            strokeWidth={2}
            dot={false}
            isAnimationActive={true}
          />
        </LineChart>
      </ResponsiveContainer>

      {signals && (
        <div className="mt-6 pt-6 border-t border-white/10 grid grid-cols-3 gap-4">
          <div className="text-center">
            <p className="text-gray-400 text-xs mb-1 font-light">Pitch Variance</p>
            <p className="text-teal-400 font-medium text-sm">
              {Math.round(signals.pitch_variance * 100)}%
            </p>
          </div>
          <div className="text-center">
            <p className="text-gray-400 text-xs mb-1 font-light">Spectral Drift</p>
            <p className="text-teal-400 font-medium text-sm">
              {Math.round(signals.spectral_drift * 100)}%
            </p>
          </div>
          <div className="text-center">
            <p className="text-gray-400 text-xs mb-1 font-light">ZCR Variance</p>
            <p className="text-teal-400 font-medium text-sm">
              {Math.round(signals.zcr_variance * 100)}%
            </p>
          </div>
        </div>
      )}
    </motion.div>
  );
}
