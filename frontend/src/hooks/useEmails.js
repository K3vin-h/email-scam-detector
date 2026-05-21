import { useState, useEffect, useCallback, useRef } from 'react';
import { api } from '../api/client.js';
import { isDemoMode } from './useAuth.js';
import { DEMO_EMAILS, filterEmails, pageEmails } from '../demo/mockData.js';

export function useEmails() {
  const demo = isDemoMode();
  const [emails, setEmails] = useState([]);
  const [count, setCount] = useState(0);
  const [page, setPage] = useState(1);
  const [filter, setFilter] = useState('');
  const [loading, setLoading] = useState(!demo);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState(null);
  const loadedRef = useRef(false);

  useEffect(() => {
    if (!demo) return;
    const filtered = filterEmails(DEMO_EMAILS, filter);
    setEmails(pageEmails(filtered, page));
    setCount(filtered.length);
    setLoading(false);
  }, [demo, page, filter]);

  const fetchEmails = useCallback(() => {
    if (demo) {
      const filtered = filterEmails(DEMO_EMAILS, filter);
      setEmails(pageEmails(filtered, page));
      setCount(filtered.length);
      return;
    }
    if (!loadedRef.current) setLoading(true);
    else setRefreshing(true);
    setError(null);
    const params = { page };
    if (filter !== '') params.risk_level = filter;
    api.getEmails(params)
      .then((data) => {
        setEmails(data.results);
        setCount(data.count);
      })
      .catch((err) => setError(err.message))
      .finally(() => {
        loadedRef.current = true;
        setLoading(false);
        setRefreshing(false);
      });
  }, [demo, page, filter]);

  useEffect(() => {
    if (demo) return;
    fetchEmails();
  }, [fetchEmails, demo]);

  const changeFilter = (newFilter) => {
    setPage(1);
    setFilter(newFilter);
  };

  const updateEmail = (gmailId, patch) => {
    setEmails((current) =>
      current.map((email) => email.gmail_id === gmailId ? { ...email, ...patch } : email)
    );
  };

  return { emails, count, page, setPage, filter, changeFilter, loading, refreshing, error, refetch: fetchEmails, updateEmail };
}
