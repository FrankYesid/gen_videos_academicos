import { useState } from 'react';
import { PlayIcon, PauseIcon } from '@heroicons/react/24/solid';

export default function VideoPlayer({
  url,
  thumbnail,
}: {
  url: string;
  thumbnail?: string;
}) {
  const [playing, setPlaying] = useState(false);

  return (
    <div className="relative aspect-video rounded-xl overflow-hidden bg-slate-900 shadow-lg">
      {url ? (
        <video
          src={url}
          poster={thumbnail}
          controls
          className="w-full h-full object-contain"
          onPlay={() => setPlaying(true)}
          onPause={() => setPlaying(false)}
        />
      ) : (
        <div className="absolute inset-0 flex flex-col items-center justify-center text-white p-6">
          <div className="w-20 h-20 rounded-full bg-white/10 backdrop-blur flex items-center justify-center mb-4 group cursor-pointer hover:bg-white/20 transition">
            <PlayIcon className="w-10 h-10 ml-1" />
          </div>
          <p className="font-medium">Vista previa del video</p>
          <p className="text-sm text-slate-400 mt-1">
            Genera el video para ver el resultado aquí.
          </p>
        </div>
      )}
      {!playing && thumbnail && (
        <button
          type="button"
          onClick={() => setPlaying(true)}
          className="absolute inset-0 flex items-center justify-center"
          aria-label="Play video"
        >
          <PauseIcon className="sr-only" />
        </button>
      )}
    </div>
  );
}
