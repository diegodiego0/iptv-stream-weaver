import { useState } from 'react';
import { Plus } from 'lucide-react';
import { IPTVConfig } from '@/types/iptv';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';

interface PlaylistModalProps {
  isOpen: boolean;
  onClose: () => void;
  config: IPTVConfig;
  onSave: (config: IPTVConfig) => void;
}

export const PlaylistModal = ({ isOpen, onClose, config, onSave }: PlaylistModalProps) => {
  const [server, setServer] = useState(config.server);
  const [username, setUsername] = useState(config.username);
  const [password, setPassword] = useState(config.password);

  const handleSave = () => {
    onSave({ server, username, password });
    onClose();
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="bg-card border-border max-w-md">
        <DialogHeader>
          <DialogTitle className="text-foreground flex items-center gap-2">
            <Plus className="w-5 h-5" />
            Configurar Playlist
          </DialogTitle>
        </DialogHeader>
        
        <div className="space-y-4 py-4">
          <div className="space-y-2">
            <Label htmlFor="server" className="text-muted-foreground">
              Servidor
            </Label>
            <Input
              id="server"
              value={server}
              onChange={(e) => setServer(e.target.value)}
              placeholder="http://servidor.com:porta"
              className="bg-secondary border-border text-foreground"
            />
          </div>
          
          <div className="space-y-2">
            <Label htmlFor="username" className="text-muted-foreground">
              Usuário
            </Label>
            <Input
              id="username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="Seu usuário"
              className="bg-secondary border-border text-foreground"
            />
          </div>
          
          <div className="space-y-2">
            <Label htmlFor="password" className="text-muted-foreground">
              Senha
            </Label>
            <Input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Sua senha"
              className="bg-secondary border-border text-foreground"
            />
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={onClose} className="border-border text-foreground">
            Cancelar
          </Button>
          <Button onClick={handleSave} className="bg-primary text-primary-foreground">
            Salvar
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};
