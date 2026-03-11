import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { toast } from "sonner";
import { supabase } from "@/supabaseClient";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

function LoginPage() {

  const navigate = useNavigate();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoading(true);

    const { error } = await supabase.auth.signInWithPassword({
      email,
      password,
    });

    setLoading(false);

    if (error) {
      toast.error(error.message);
      return;
    }

    toast.success("Connexion réussie");
    navigate("/dashboard");
  };

  const handleSignup = async () => {

    const { error } = await supabase.auth.signUp({
      email,
      password,
    });

    if (error) {
      toast.error(error.message);
      return;
    }

    toast.success("Compte créé, vérifiez votre email.");
  };

  return (
    <div className="flex items-center justify-center min-h-screen bg-gray-50">

      <form
        onSubmit={handleLogin}
        className="w-full max-w-sm p-6 space-y-4 bg-white rounded-xl shadow"
      >

        <h1 className="text-xl font-semibold text-center">
          Connexion
        </h1>

        <div className="space-y-2">
          <Label>Email</Label>
          <Input
            type="email"
            placeholder="email@exemple.com"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
        </div>

        <div className="space-y-2">
          <Label>Mot de passe</Label>
          <Input
            type="password"
            placeholder="********"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
        </div>

        <Button
          type="submit"
          disabled={loading}
          className="w-full"
        >
          {loading ? "Connexion..." : "Se connecter"}
        </Button>

        <Button
          type="button"
          variant="outline"
          className="w-full"
          onClick={handleSignup}
        >
          Créer un compte
        </Button>

      </form>

    </div>
  );
}

export default LoginPage;
