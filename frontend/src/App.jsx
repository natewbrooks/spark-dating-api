import { useState } from 'react'
import TitleBarComponent from './components/TitleBarComponent'
import PhoneAuthFormComponent from './components/PhoneAuthFormComponent'
import './index.css'

export default function App() {
    return (
        <section className='flex flex-col w-full h-full'>
            <header>
                <TitleBarComponent/>
            </header>
            <main className='flex w-full justify-center '>
                <PhoneAuthFormComponent/>
            </main>
            <footer>
            </footer>
        </section>
    )
}