'use client';

import { useState, useEffect, useRef } from 'react';
import { useRouter } from 'next/navigation';
import { createClient } from '@/lib/supabase/client'; 

export default function QuizPage() {
  const [questionData, setQuestionData] = useState<any>(null);
  const [questionNumber, setQuestionNumber] = useState(1);
  const [questionStartTime, setQuestionStartTime] = useState(Date.now());
  const [logs, setLogs] = useState<any[]>([]);
  const [score, setScore] = useState(0);
  
  const router = useRouter();
  const supabase = createClient();
  const sessionId = useRef(`sess_${Math.random().toString(36).substr(2, 9)}`);

  const fetchQuestion = async (difficulty: number) => {
    try {
      const res = await fetch(`http://localhost:8000/generate-question?difficulty=${difficulty}&session_id=${sessionId.current}`);
      const data = await res.json();
      setQuestionData(data);
      setQuestionStartTime(Date.now());
    } catch (error) {
      console.error("Error fetching question:", error);
    }
  };

  useEffect(() => {
    fetchQuestion(1); 
  }, []);

  const handleAnswer = async (selectedIndex: number) => {
    const timeTaken = (Date.now() - questionStartTime) / 1000;
    const isCorrect = selectedIndex === questionData.answer;
    const newScore = score + (isCorrect ? 1 : 0);
    
    if (isCorrect) setScore(newScore);

    const newLog = {
      q_number: questionNumber,
      topic: questionData.topic || "chemical bonding",
      difficulty: 1, 
      is_correct: isCorrect,
      time_taken: timeTaken
    };

    const updatedLogs = [...logs, newLog];
    setLogs(updatedLogs);

    if (questionNumber >= 10) { 
      await submitQuiz(updatedLogs, newScore);
    } else {
      setQuestionNumber(prev => prev + 1);
      fetchQuestion(isCorrect ? 2 : 1); 
    }
  };

  const submitQuiz = async (finalLogs: any[], finalScore: number) => {
    const { data: { user } } = await supabase.auth.getUser();
    if (!user) return;

    const payload = {
      student_name: user.user_metadata?.full_name || "Student",
      student_email: user.email,
      session_id: sessionId.current,
      session_data: { score: finalScore, total_questions: finalLogs.length, violations: 0 },
      question_logs: finalLogs
    };

    const response = await fetch("http://localhost:8000/api/submit-quiz", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });

    if (response.ok) {
      await supabase.from('users').update({ has_taken_diagnostic: true }).eq('id', user.id);
      router.push('/dashboard');
    }
  };

  if (!questionData) return <div className="p-10 text-center">Loading Assessment...</div>;

  return (
    <div className="max-w-2xl mx-auto p-8 mt-10 shadow-lg rounded">
      <h2 className="text-xl mb-4">Question {questionNumber} of 10</h2>
      <p className="text-2xl font-bold mb-6">{questionData?.question}</p>
      <div className="flex flex-col gap-3">
        {questionData?.options.map((opt: string, idx: number) => (
          <button key={idx} onClick={() => handleAnswer(idx)} className="p-4 border rounded text-left hover:bg-gray-50">
            {opt}
          </button>
        ))}
      </div>
    </div>
  );
}
