import * as React from "react"
import { Slot } from "@radix-ui/react-slot"
import { cva, type VariantProps } from "class-variance-authority"

import { cn } from "../../lib/utils"

const buttonVariants = cva(
  "inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-lg text-sm font-medium transition-all duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 [&_svg]:pointer-events-none [&_svg]:size-4 [&_svg]:shrink-0",
  {
    variants: {
      variant: {
        default: "bg-primary-600 text-white hover:bg-primary-700 shadow-md hover:shadow-lg hover:scale-102",
        primary: "bg-primary-600 text-white hover:bg-primary-700 shadow-md hover:shadow-lg hover:scale-102",
        destructive:
          "bg-red-600 text-white hover:bg-red-700 shadow-md hover:shadow-lg hover:scale-102",
        danger:
          "bg-red-600 text-white hover:bg-red-700 shadow-md hover:shadow-lg hover:scale-102",
        success:
          "bg-green-600 text-white hover:bg-green-700 shadow-md hover:shadow-lg hover:scale-102",
        outline:
          "border-2 border-gray-300 bg-white hover:bg-gray-50 hover:border-gray-400 shadow-sm hover:shadow",
        secondary:
          "bg-secondary-600 text-white hover:bg-secondary-700 shadow-md hover:shadow-lg hover:scale-102",
        ghost: "hover:bg-gray-100",
        link: "text-primary-600 underline-offset-4 hover:underline",
      },
      size: {
        default: "h-10 px-4 py-2",
        sm: "h-9 rounded-lg px-3 text-xs",
        lg: "h-12 rounded-lg px-8 text-base",
        icon: "h-10 w-10",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  }
)

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, asChild = false, ...props }, ref) => {
    const Comp = asChild ? Slot : "button"
    return (
      <Comp
        className={cn(buttonVariants({ variant, size, className }))}
        ref={ref}
        {...props}
      />
    )
  }
)
Button.displayName = "Button"

export { Button, buttonVariants }
