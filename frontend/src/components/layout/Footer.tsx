import React, { useMemo } from 'react';
import { IonNote } from '@ionic/react';
import style from './layout.module.scss';

export const Footer: React.FC = () => {
  const version = useMemo(() => import.meta.env.VITE_GIT_TAG, [])

  return (
    <footer className={ style.footer }>
      <div>
        <IonNote color="medium">{ version }</IonNote>
      </div>

      <div></div>
    </footer>
  );
};
