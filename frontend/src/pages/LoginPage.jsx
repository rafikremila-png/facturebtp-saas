import { useState, useEffect } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { toast } from "sonner";
import { supabase } from "@/supabaseClient"; // ← NOUVEAU
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/

