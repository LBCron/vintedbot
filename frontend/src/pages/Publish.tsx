import { useState, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Calendar as CalendarIcon,
  ChevronLeft,
  ChevronRight,
  Clock,
  Send,
  Filter,
  Grid3x3,
  List,
  Plus,
  Check,
  AlertCircle,
  Trash2,
  Edit,
  PlayCircle,
} from 'lucide-react';
import { Badge } from '../components/common/Badge';
import { Tooltip } from '../components/common/Tooltip';

interface ScheduledDraft {
  id: string;
  title: string;
  thumbnail: string;
  price: number;
  scheduledDate: Date;
  scheduledTime: string;
  status: 'scheduled' | 'publishing' | 'published' | 'failed';
  account?: string;
}

interface TimeSlot {
  time: string;
  draft?: ScheduledDraft;
}

const mockScheduledDrafts: ScheduledDraft[] = [
  {
    id: '1',
    title: 'Nike Air Max 90',
    thumbnail: 'https://via.placeholder.com/100',
    price: 89.99,
    scheduledDate: new Date(2025, 10, 12, 10, 0),
    scheduledTime: '10:00',
    status: 'scheduled',
    account: 'Main Account',
  },
  {
    id: '2',
    title: 'Adidas Hoodie Vintage',
    thumbnail: 'https://via.placeholder.com/100',
    price: 45.00,
    scheduledDate: new Date(2025, 10, 13, 14, 30),
    scheduledTime: '14:30',
    status: 'scheduled',
    account: 'Main Account',
  },
  {
    id: '3',
    title: 'Levi\'s 501 Jeans',
    thumbnail: 'https://via.placeholder.com/100',
    price: 65.00,
    scheduledDate: new Date(2025, 10, 14, 9, 0),
    scheduledTime: '09:00',
    status: 'scheduled',
    account: 'Secondary Account',
  },
];

const timeSlots = [
  '09:00', '10:00', '11:00', '12:00', '13:00', '14:00',
  '15:00', '16:00', '17:00', '18:00', '19:00', '20:00'
];

export default function Publish() {
  const [currentDate, setCurrentDate] = useState(new Date());
  const [viewMode, setViewMode] = useState<'calendar' | 'list'>('calendar');
  const [scheduledDrafts, setScheduledDrafts] = useState<ScheduledDraft[]>(mockScheduledDrafts);
  const [selectedDate, setSelectedDate] = useState<Date | null>(null);
  const [draggedDraft, setDraggedDraft] = useState<ScheduledDraft | null>(null);

  // Get days in current month
  const daysInMonth = useMemo(() => {
    const year = currentDate.getFullYear();
    const month = currentDate.getMonth();
    const firstDay = new Date(year, month, 1);
    const lastDay = new Date(year, month + 1, 0);
    const daysCount = lastDay.getDate();
    const startingDayOfWeek = firstDay.getDay();

    const days: (Date | null)[] = [];

    // Add empty cells for days before month starts
    for (let i = 0; i < startingDayOfWeek; i++) {
      days.push(null);
    }

    // Add days of month
    for (let i = 1; i <= daysCount; i++) {
      days.push(new Date(year, month, i));
    }

    return days;
  }, [currentDate]);

  const getDraftsForDate = (date: Date | null) => {
    if (!date) return [];
    return scheduledDrafts.filter(draft =>
      draft.scheduledDate.toDateString() === date.toDateString()
    );
  };

  const handlePreviousMonth = () => {
    setCurrentDate(new Date(currentDate.getFullYear(), currentDate.getMonth() - 1, 1));
  };

  const handleNextMonth = () => {
    setCurrentDate(new Date(currentDate.getFullYear(), currentDate.getMonth() + 1, 1));
  };

  const handleDragStart = (draft: ScheduledDraft) => {
    setDraggedDraft(draft);
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
  };

  const handleDrop = (date: Date | null, time?: string) => {
    if (!draggedDraft || !date) return;

    setScheduledDrafts(prev =>
      prev.map(draft =>
        draft.id === draggedDraft.id
          ? { ...draft, scheduledDate: date, scheduledTime: time || draft.scheduledTime }
          : draft
      )
    );
    setDraggedDraft(null);
  };

  const getStatusColor = (status: ScheduledDraft['status']) => {
    switch (status) {
      case 'scheduled': return 'primary';
      case 'publishing': return 'warning';
      case 'published': return 'success';
      case 'failed': return 'error';
      default: return 'default';
    }
  };

  const getStatusIcon = (status: ScheduledDraft['status']) => {
    switch (status) {
      case 'scheduled': return Clock;
      case 'publishing': return PlayCircle;
      case 'published': return Check;
      case 'failed': return AlertCircle;
      default: return Clock;
    }
  };

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex items-center justify-between"
      >
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
            📅 Publishing Schedule
          </h1>
          <p className="text-gray-600 dark:text-gray-400 mt-2">
            Plan and automate your Vinted listings
          </p>
        </div>

        <div className="flex items-center gap-3">
          {/* View Mode Toggle */}
          <div className="flex items-center gap-2 p-1 bg-gray-100 dark:bg-gray-800 rounded-lg">
            <button
              onClick={() => setViewMode('calendar')}
              className={`p-2 rounded-lg transition-colors ${
                viewMode === 'calendar'
                  ? 'bg-white dark:bg-gray-700 text-primary-600 dark:text-primary-400 shadow-sm'
                  : 'text-gray-500 hover:text-gray-700 dark:hover:text-gray-300'
              }`}
              title="Calendar view"
            >
              <Grid3x3 className="w-5 h-5" />
            </button>
            <button
              onClick={() => setViewMode('list')}
              className={`p-2 rounded-lg transition-colors ${
                viewMode === 'list'
                  ? 'bg-white dark:bg-gray-700 text-primary-600 dark:text-primary-400 shadow-sm'
                  : 'text-gray-500 hover:text-gray-700 dark:hover:text-gray-300'
              }`}
              title="List view"
            >
              <List className="w-5 h-5" />
            </button>
          </div>

          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            className="px-6 py-3 bg-primary-500 hover:bg-primary-600 text-white rounded-lg flex items-center gap-2 font-medium shadow-lg transition-colors"
          >
            <Plus className="w-5 h-5" />
            Schedule Draft
          </motion.button>
        </div>
      </motion.div>

      {/* Stats Cards */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.1 }}
        className="grid grid-cols-1 md:grid-cols-4 gap-4"
      >
        {[
          { label: 'Scheduled', value: scheduledDrafts.filter(d => d.status === 'scheduled').length, color: 'primary', icon: Clock },
          { label: 'Publishing Today', value: scheduledDrafts.filter(d => d.scheduledDate.toDateString() === new Date().toDateString()).length, color: 'warning', icon: PlayCircle },
          { label: 'Published', value: scheduledDrafts.filter(d => d.status === 'published').length, color: 'success', icon: Check },
          { label: 'Failed', value: scheduledDrafts.filter(d => d.status === 'failed').length, color: 'error', icon: AlertCircle },
        ].map((stat, index) => (
          <motion.div
            key={stat.label}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 + index * 0.05 }}
            className="card p-6"
          >
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400">{stat.label}</p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white mt-1">
                  {stat.value}
                </p>
              </div>
              <div className={`p-3 bg-${stat.color}-100 dark:bg-${stat.color}-900/20 rounded-xl`}>
                <stat.icon className={`w-6 h-6 text-${stat.color}-600 dark:text-${stat.color}-400`} />
              </div>
            </div>
          </motion.div>
        ))}
      </motion.div>

      {viewMode === 'calendar' ? (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.2 }}
          className="card p-6"
        >
          {/* Calendar Header */}
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-xl font-bold text-gray-900 dark:text-white">
              {currentDate.toLocaleDateString('en-US', { month: 'long', year: 'numeric' })}
            </h2>
            <div className="flex items-center gap-2">
              <button
                onClick={handlePreviousMonth}
                className="p-2 text-gray-600 hover:text-gray-900 dark:text-gray-400 dark:hover:text-white hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors"
              >
                <ChevronLeft className="w-5 h-5" />
              </button>
              <button
                onClick={() => setCurrentDate(new Date())}
                className="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors"
              >
                Today
              </button>
              <button
                onClick={handleNextMonth}
                className="p-2 text-gray-600 hover:text-gray-900 dark:text-gray-400 dark:hover:text-white hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors"
              >
                <ChevronRight className="w-5 h-5" />
              </button>
            </div>
          </div>

          {/* Calendar Grid */}
          <div className="grid grid-cols-7 gap-2">
            {/* Day headers */}
            {['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].map(day => (
              <div key={day} className="text-center text-sm font-semibold text-gray-600 dark:text-gray-400 py-2">
                {day}
              </div>
            ))}

            {/* Calendar days */}
            {daysInMonth.map((day, index) => {
              const draftsForDay = getDraftsForDate(day);
              const isToday = day && day.toDateString() === new Date().toDateString();
              const isSelected = selectedDate && day && day.toDateString() === selectedDate.toDateString();

              return (
                <div
                  key={index}
                  onDragOver={handleDragOver}
                  onDrop={(e) => {
                    e.preventDefault();
                    handleDrop(day);
                  }}
                  onClick={() => day && setSelectedDate(day)}
                  className={`min-h-[100px] p-2 border-2 rounded-lg transition-all cursor-pointer ${
                    day
                      ? isSelected
                        ? 'border-primary-500 bg-primary-50 dark:bg-primary-900/20'
                        : isToday
                        ? 'border-primary-300 dark:border-primary-700 bg-primary-50/50 dark:bg-primary-900/10'
                        : 'border-gray-200 dark:border-gray-700 hover:border-primary-300 dark:hover:border-primary-700 hover:bg-gray-50 dark:hover:bg-gray-800'
                      : 'border-transparent'
                  }`}
                >
                  {day && (
                    <>
                      <div className={`text-sm font-medium mb-1 ${
                        isToday
                          ? 'text-primary-600 dark:text-primary-400'
                          : 'text-gray-700 dark:text-gray-300'
                      }`}>
                        {day.getDate()}
                      </div>
                      <div className="space-y-1">
                        {draftsForDay.slice(0, 2).map((draft) => (
                          <Tooltip key={draft.id} content={`${draft.title} - ${draft.scheduledTime}`}>
                            <div
                              draggable
                              onDragStart={() => handleDragStart(draft)}
                              className="text-xs p-1.5 bg-primary-100 dark:bg-primary-900/40 text-primary-700 dark:text-primary-300 rounded truncate cursor-move hover:bg-primary-200 dark:hover:bg-primary-900/60 transition-colors"
                            >
                              {draft.scheduledTime} - {draft.title.substring(0, 15)}...
                            </div>
                          </Tooltip>
                        ))}
                        {draftsForDay.length > 2 && (
                          <div className="text-xs text-gray-500 dark:text-gray-400 pl-1">
                            +{draftsForDay.length - 2} more
                          </div>
                        )}
                      </div>
                    </>
                  )}
                </div>
              );
            })}
          </div>
        </motion.div>
      ) : (
        /* List View */
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.2 }}
          className="space-y-3"
        >
          <AnimatePresence>
            {scheduledDrafts
              .sort((a, b) => a.scheduledDate.getTime() - b.scheduledDate.getTime())
              .map((draft, index) => {
                const StatusIcon = getStatusIcon(draft.status);
                return (
                  <motion.div
                    key={draft.id}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    exit={{ opacity: 0, x: 20 }}
                    transition={{ delay: index * 0.05 }}
                    className="card p-6 hover:shadow-lg transition-shadow"
                  >
                    <div className="flex items-center gap-6">
                      {/* Thumbnail */}
                      <img
                        src={draft.thumbnail}
                        alt={draft.title}
                        className="w-20 h-20 object-cover rounded-lg"
                      />

                      {/* Info */}
                      <div className="flex-1">
                        <h3 className="font-semibold text-gray-900 dark:text-white mb-1">
                          {draft.title}
                        </h3>
                        <div className="flex items-center gap-3 text-sm text-gray-600 dark:text-gray-400">
                          <span className="flex items-center gap-1">
                            <CalendarIcon className="w-4 h-4" />
                            {draft.scheduledDate.toLocaleDateString()}
                          </span>
                          <span className="flex items-center gap-1">
                            <Clock className="w-4 h-4" />
                            {draft.scheduledTime}
                          </span>
                          <span className="font-medium text-gray-900 dark:text-white">
                            €{draft.price.toFixed(2)}
                          </span>
                        </div>
                        {draft.account && (
                          <div className="mt-2">
                            <Badge variant="default" size="sm">
                              {draft.account}
                            </Badge>
                          </div>
                        )}
                      </div>

                      {/* Status */}
                      <div className="flex items-center gap-3">
                        <Badge variant={getStatusColor(draft.status)} size="md" dot>
                          <StatusIcon className="w-4 h-4 mr-1" />
                          {draft.status.charAt(0).toUpperCase() + draft.status.slice(1)}
                        </Badge>

                        {/* Actions */}
                        <div className="flex items-center gap-1">
                          <button className="p-2 text-gray-400 hover:text-primary-500 hover:bg-primary-50 dark:hover:bg-primary-900/20 rounded-lg transition-colors">
                            <Edit className="w-4 h-4" />
                          </button>
                          <button className="p-2 text-gray-400 hover:text-error-500 hover:bg-error-50 dark:hover:bg-error-900/20 rounded-lg transition-colors">
                            <Trash2 className="w-4 h-4" />
                          </button>
                        </div>
                      </div>
                    </div>
                  </motion.div>
                );
              })}
          </AnimatePresence>
        </motion.div>
      )}

      {/* Day Detail Drawer (when date selected) */}
      <AnimatePresence>
        {selectedDate && viewMode === 'calendar' && (
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: 20 }}
            className="fixed right-0 top-0 h-full w-96 bg-white dark:bg-gray-900 shadow-2xl p-6 overflow-y-auto z-50"
          >
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-xl font-bold text-gray-900 dark:text-white">
                {selectedDate.toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric' })}
              </h3>
              <button
                onClick={() => setSelectedDate(null)}
                className="p-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
              >
                ✕
              </button>
            </div>

            <div className="space-y-3">
              {timeSlots.map(time => {
                const draft = getDraftsForDate(selectedDate).find(d => d.scheduledTime === time);
                return (
                  <div
                    key={time}
                    onDragOver={handleDragOver}
                    onDrop={(e) => {
                      e.preventDefault();
                      handleDrop(selectedDate, time);
                    }}
                    className={`p-4 border-2 border-dashed rounded-lg transition-all ${
                      draft
                        ? 'border-primary-300 dark:border-primary-700 bg-primary-50 dark:bg-primary-900/20'
                        : 'border-gray-200 dark:border-gray-700 hover:border-primary-300 dark:hover:border-primary-600'
                    }`}
                  >
                    <div className="flex items-center gap-2 mb-2">
                      <Clock className="w-4 h-4 text-gray-500" />
                      <span className="text-sm font-medium text-gray-700 dark:text-gray-300">{time}</span>
                    </div>
                    {draft ? (
                      <div
                        draggable
                        onDragStart={() => handleDragStart(draft)}
                        className="flex items-center gap-3 p-2 bg-white dark:bg-gray-800 rounded-lg cursor-move"
                      >
                        <img src={draft.thumbnail} alt={draft.title} className="w-10 h-10 object-cover rounded" />
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-medium text-gray-900 dark:text-white truncate">
                            {draft.title}
                          </p>
                          <p className="text-xs text-gray-600 dark:text-gray-400">
                            €{draft.price.toFixed(2)}
                          </p>
                        </div>
                      </div>
                    ) : (
                      <p className="text-sm text-gray-500 dark:text-gray-400">Drop a draft here</p>
                    )}
                  </div>
                );
              })}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
