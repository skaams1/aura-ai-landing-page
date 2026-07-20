'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { createClient } from '@/lib/supabase/client'; 

export default function SignUpPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [name, setName] = useState('');
  const router = useRouter();
  const supabase = createClient();

  const handleSignUp = async (e: React.FormEvent) => {
    e.preventDefault();

    // Sign up the user in Supabase
    const { data, error } = await supabase.auth.signUp({
      email,
      password,
      options: { data: { full_name: name } }
    });

    if (error) {
      alert("Signup failed: " + error.message);
      return;
    }

    // Instantly push them to the quiz
    if (data.user) {
      router.push('/quiz');
    }
  };

  return (
    <div className="flex justify-center items-center h-screen">
      <form onSubmit={handleSignUp} className="p-8 bg-white shadow-md rounded flex flex-col gap-4 w-96">
        <h2 className="text-2xl font-bold">Create Account</h2>
        <input type="text" value={name} onChange={(e) => setName(e.target.value)} placeholder="Full Name" required className="p-2 border rounded" />
        <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="Email" required className="p-2 border rounded" />
        <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="Password" required className="p-2 border rounded" />
        <button type="submit" className="bg-blue-600 text-white p-2 rounded">Sign Up</button>
      </form>
    </div>
  );
}
