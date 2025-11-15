import { motion, useSpring, useTransform, MotionValue } from 'framer-motion';
import { useEffect } from 'react';

interface AnimatedNumberProps {
  value: number;
  duration?: number;
  className?: string;
}

export function AnimatedNumber({ value, duration = 2, className }: AnimatedNumberProps) {
  const spring = useSpring(0, {
    duration: duration * 1000,
    bounce: 0.2
  });

  const display = useTransform(spring, (current) =>
    Math.round(current).toLocaleString()
  );

  useEffect(() => {
    spring.set(value);
  }, [value, spring]);

  return <motion.span className={className}>{display}</motion.span>;
}

export function AnimatedCurrency({ value, duration = 2, currency = '€' }: AnimatedNumberProps & { currency?: string }) {
  const spring = useSpring(0, { duration: duration * 1000 });
  const display = useTransform(spring, (current) =>
    `${Math.round(current).toLocaleString()}${currency}`
  );

  useEffect(() => {
    spring.set(value);
  }, [value, spring]);

  return <motion.span>{display}</motion.span>;
}
