/**
 * Hook for managing drafts with optimized loading and caching
 */
import { useState, useCallback } from 'react';
import { bulkAPI } from '../api/client';
import type { Draft } from '../types';

interface UseDraftsReturn {
  drafts: Draft[];
  loading: boolean;
  error: Error | null;
  loadDrafts: (params?: any) => Promise<void>;
  publishDraft: (id: string) => Promise<boolean>;
  deleteDraft: (id: string) => Promise<boolean>;
  bulkPublish: (ids: string[]) => Promise<boolean>;
  bulkDelete: (ids: string[]) => Promise<boolean>;
}

export function useDrafts(): UseDraftsReturn {
  const [drafts, setDrafts] = useState<Draft[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const loadDrafts = useCallback(async (params: any = {}) => {
    try {
      setLoading(true);
      setError(null);
      const response = await bulkAPI.getDrafts(params);
      setDrafts(response.data.drafts);
    } catch (err) {
      setError(err instanceof Error ? err : new Error('Failed to load drafts'));
    } finally {
      setLoading(false);
    }
  }, []);

  const publishDraft = useCallback(async (id: string): Promise<boolean> => {
    try {
      await bulkAPI.publishDraft(id);
      setDrafts(prev => prev.filter(d => d.id !== id));
      return true;
    } catch (err) {
      setError(err instanceof Error ? err : new Error(`Failed to publish draft ${id}`));
      return false;
    }
  }, []);

  const deleteDraft = useCallback(async (id: string): Promise<boolean> => {
    try {
      await bulkAPI.deleteDraft(id);
      setDrafts(prev => prev.filter(d => d.id !== id));
      return true;
    } catch (err) {
      setError(err instanceof Error ? err : new Error(`Failed to delete draft ${id}`));
      return false;
    }
  }, []);

  const bulkPublish = useCallback(async (ids: string[]): Promise<boolean> => {
    try {
      await Promise.all(ids.map(id => bulkAPI.publishDraft(id)));
      setDrafts(prev => prev.filter(d => !ids.includes(d.id)));
      return true;
    } catch (err) {
      setError(err instanceof Error ? err : new Error('Failed to bulk publish'));
      return false;
    }
  }, []);

  const bulkDelete = useCallback(async (ids: string[]): Promise<boolean> => {
    try {
      await Promise.all(ids.map(id => bulkAPI.deleteDraft(id)));
      setDrafts(prev => prev.filter(d => !ids.includes(d.id)));
      return true;
    } catch (err) {
      setError(err instanceof Error ? err : new Error('Failed to bulk delete'));
      return false;
    }
  }, []);

  return {
    drafts,
    loading,
    error,
    loadDrafts,
    publishDraft,
    deleteDraft,
    bulkPublish,
    bulkDelete,
  };
}
