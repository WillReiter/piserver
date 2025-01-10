'use client';
import { Button } from "@/components/ui/button"



export default function Home() {
    const handleClick = () => {
        fetch("/py/toggle")
    }
    return (
        <Button onClick={handleClick}>Toggle Light</Button>
    )
}

