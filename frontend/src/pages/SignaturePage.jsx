import React, { useRef, useState, useEffect } from 'react';
import { useParams, useSearchParams } from 'react-router-dom';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Loader2, Check, PenTool, RefreshCw, FileText, AlertCircle } from 'lucide-react';
import { toast } from 'sonner';
import axios from 'axios';

const API = process.env.REACT_APP_BACKEND_URL;

const SignaturePage = () => {
    const { token } = useParams();
    const [searchParams] = useSearchParams();
    const canvasRef = useRef(null);
    const [isDrawing, setIsDrawing] = useState(false);
    const [loading, setLoading] = useState(true);
    const [signing, setSigning] = useState(false);
    const [signatureData, setSignatureData] = useState(null);
    const [signatureStatus, setSignatureStatus] = useState(null);
    const [error, setError] = useState(null);

    useEffect(() => {
        checkSignatureStatus();
    }, [token]);

    const checkSignatureStatus = async () => {
        try {
            const response = await axios.get(`${API}/api/signatures/status/${token}`);
            setSignatureStatus(response.data);
            setLoading(false);
        } catch (err) {
            setError('Lien de signature invalide ou expiré');
            setLoading(false);
        }
    };

    useEffect(() => {
        const canvas = canvasRef.current;
        if (!canvas) return;

        const ctx = canvas.getContext('2d');
        ctx.fillStyle = 'white';
        ctx.fillRect(0, 0, canvas.width, canvas.height);
        ctx.strokeStyle = '#1e40af';
        ctx.lineWidth = 2;
        ctx.lineCap = 'round';
        ctx.lineJoin = 'round';
    }, [signatureStatus]);

    const getCoordinates = (e) => {
        const canvas = canvasRef.current;
        const rect = canvas.getBoundingClientRect();
        const scaleX = canvas.width / rect.width;
        const scaleY = canvas.height / rect.height;

        if (e.touches) {
            return {
                x: (e.touches[0].clientX - rect.left) * scaleX,
                y: (e.touches[0].clientY - rect.top) * scaleY
            };
        }
        return {
            x: (e.clientX - rect.left) * scaleX,
            y: (e.clientY - rect.top) * scaleY
        };
    };

    const startDrawing = (e) => {
        e.preventDefault();
        const canvas = canvasRef.current;
        const ctx = canvas.getContext('2d');
        const { x, y } = getCoordinates(e);
        
        ctx.beginPath();
        ctx.moveTo(x, y);
        setIsDrawing(true);
    };

    const draw = (e) => {
        if (!isDrawing) return;
        e.preventDefault();
        
        const canvas = canvasRef.current;
        const ctx = canvas.getContext('2d');
        const { x, y } = getCoordinates(e);
        
        ctx.lineTo(x, y);
        ctx.stroke();
    };

    const stopDrawing = () => {
        setIsDrawing(false);
    };

    const clearCanvas = () => {
        const canvas = canvasRef.current;
        const ctx = canvas.getContext('2d');
        ctx.fillStyle = 'white';
        ctx.fillRect(0, 0, canvas.width, canvas.height);
        setSignatureData(null);
    };

    const handleSign = async () => {
        const canvas = canvasRef.current;
        const dataUrl = canvas.toDataURL('image/png');
        
        // Check if canvas has any drawing
        const ctx = canvas.getContext('2d');
        const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
        const pixels = imageData.data;
        let hasDrawing = false;
        
        for (let i = 0; i < pixels.length; i += 4) {
            // Check if pixel is not white
            if (pixels[i] < 250 || pixels[i + 1] < 250 || pixels[i + 2] < 250) {
                hasDrawing = true;
                break;
            }
        }
        
        if (!hasDrawing) {
            toast.error('Veuillez dessiner votre signature');
            return;
        }

        setSigning(true);
        try {
            const response = await axios.post(`${API}/api/signatures/sign/${token}`, {
                signature_data: dataUrl
            });
            
            toast.success('Document signé avec succès !');
            setSignatureStatus({ ...signatureStatus, status: 'signed', signed_at: response.data.signed_at });
        } catch (err) {
            toast.error(err.response?.data?.detail || 'Erreur lors de la signature');
        } finally {
            setSigning(false);
        }
    };

    if (loading) {
        return (
            <div className="min-h-screen bg-gray-50 flex items-center justify-center">
                <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
            </div>
        );
    }

    if (error || !signatureStatus?.valid) {
        return (
            <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
                <Card className="max-w-md w-full">
                    <CardContent className="pt-6 text-center">
                        <AlertCircle className="h-16 w-16 text-red-500 mx-auto mb-4" />
                        <h2 className="text-xl font-bold text-gray-900 mb-2">Lien invalide</h2>
                        <p className="text-gray-600">
                            {error || 'Ce lien de signature est invalide ou a expiré.'}
                        </p>
                    </CardContent>
                </Card>
            </div>
        );
    }

    if (signatureStatus.status === 'signed') {
        return (
            <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
                <Card className="max-w-md w-full">
                    <CardContent className="pt-6 text-center">
                        <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
                            <Check className="h-8 w-8 text-green-600" />
                        </div>
                        <h2 className="text-xl font-bold text-gray-900 mb-2">Document signé</h2>
                        <p className="text-gray-600 mb-4">
                            Ce document a été signé le {new Date(signatureStatus.signed_at).toLocaleDateString('fr-FR', {
                                day: 'numeric',
                                month: 'long',
                                year: 'numeric',
                                hour: '2-digit',
                                minute: '2-digit'
                            })}.
                        </p>
                        <Badge variant="secondary" className="text-green-600">
                            <Check className="h-3 w-3 mr-1" /> Signature validée
                        </Badge>
                    </CardContent>
                </Card>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-gray-50 py-8 px-4">
            <div className="max-w-2xl mx-auto">
                <Card>
                    <CardHeader className="text-center">
                        <div className="flex justify-center mb-4">
                            <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center">
                                <PenTool className="h-8 w-8 text-blue-600" />
                            </div>
                        </div>
                        <CardTitle className="text-2xl">Signature électronique</CardTitle>
                        <CardDescription>
                            {signatureStatus.client_name}, veuillez signer le document ci-dessous
                        </CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-6">
                        <div className="bg-gray-50 rounded-lg p-4">
                            <div className="flex items-center gap-2 text-sm text-gray-600 mb-2">
                                <FileText className="h-4 w-4" />
                                Document à signer
                            </div>
                            <p className="text-gray-900 font-medium">
                                En signant ce document, vous acceptez les termes et conditions du devis.
                            </p>
                        </div>

                        <div className="space-y-3">
                            <div className="flex justify-between items-center">
                                <label className="text-sm font-medium text-gray-700">
                                    Dessinez votre signature
                                </label>
                                <Button
                                    variant="ghost"
                                    size="sm"
                                    onClick={clearCanvas}
                                    className="text-gray-500"
                                >
                                    <RefreshCw className="h-4 w-4 mr-1" />
                                    Effacer
                                </Button>
                            </div>
                            
                            <div className="border-2 border-gray-200 rounded-lg overflow-hidden bg-white">
                                <canvas
                                    ref={canvasRef}
                                    width={600}
                                    height={200}
                                    className="w-full touch-none cursor-crosshair"
                                    onMouseDown={startDrawing}
                                    onMouseMove={draw}
                                    onMouseUp={stopDrawing}
                                    onMouseLeave={stopDrawing}
                                    onTouchStart={startDrawing}
                                    onTouchMove={draw}
                                    onTouchEnd={stopDrawing}
                                />
                            </div>
                            <p className="text-xs text-gray-500 text-center">
                                Utilisez votre souris ou votre doigt pour dessiner
                            </p>
                        </div>

                        <Button
                            onClick={handleSign}
                            disabled={signing}
                            className="w-full"
                            size="lg"
                        >
                            {signing ? (
                                <>
                                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                                    Signature en cours...
                                </>
                            ) : (
                                <>
                                    <Check className="mr-2 h-4 w-4" />
                                    Signer le document
                                </>
                            )}
                        </Button>

                        <p className="text-xs text-gray-500 text-center">
                            En cliquant sur "Signer le document", vous certifiez que vous êtes bien {signatureStatus.client_name} 
                            et vous acceptez que cette signature électronique a la même valeur légale qu'une signature manuscrite.
                        </p>
                    </CardContent>
                </Card>
            </div>
        </div>
    );
};

export default SignaturePage;
